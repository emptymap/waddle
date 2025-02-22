import concurrent.futures
import os
import shutil
from pathlib import Path
from typing import Any

from waddle.audios.align_offset import align_speaker_to_reference
from waddle.audios.call_tools import (
    convert_all_files_to_wav,
    convert_to_wav,
    remove_noise,
)
from waddle.audios.clip import clip_audio
from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_LANGUAGE, DEFAULT_OUT_AUDIO_DURATION
from waddle.processing.combine import (
    combine_audio_files,
    combine_segments_into_audio_with_timeline,
    combine_srt_files,
    merge_timelines,
)
from waddle.processing.segment import (
    SpeechTimeline,
    detect_speech_timeline,
    process_segments,
)
from waddle.utils import to_path


def select_reference_audio(audio_paths: list[Path]) -> Path:
    """
    Automatically select a reference audio file starting with 'GMT'.

    Args:
        audio_paths (list): List of audio file paths.

    Returns:
        str: Path to the reference audio file.
    """
    gmt_files = [f for f in audio_paths if Path(f).name.startswith("GMT")]
    if not gmt_files:
        raise ValueError("No reference audio file found and no GMT file exists.")
    return gmt_files[0]


def prepare_audio_file(
    audio_path: Path,
    ss: float = 0.0,
    out_duration: float | None = None,
) -> Path:
    """Prepare audio file by converting, clipping and removing noise."""
    if audio_path.suffix != ".wav":
        convert_to_wav(audio_path)
        audio_path = audio_path.with_suffix(".wav")
    clip_audio(audio_path, audio_path, ss=ss, out_duration=out_duration)
    remove_noise(audio_path, audio_path)
    return audio_path


def create_output_paths(
    output_dir: Path,
    speaker_audio: Path,
) -> tuple[Path, Path]:
    """Create output paths for processed audio and transcription."""
    speaker_name = speaker_audio.stem
    return (output_dir / f"{speaker_name}.wav", output_dir / f"{speaker_name}.srt")


def process_single_file(
    aligned_audio: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    speaker_audio: str | bytes | os.PathLike[Any],
    ss: float = 0.0,
    out_duration: float | None = None,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> Path:
    """Process a single audio file: normalize, detect speech, and transcribe."""
    aligned_audio_path = to_path(aligned_audio)
    output_dir_path = to_path(output_dir)
    speaker_audio_path = to_path(speaker_audio)

    # Prepare audio file
    aligned_audio_path = prepare_audio_file(aligned_audio_path, ss, out_duration)

    # Detect speech segments
    segs_folder_path, _ = detect_speech_timeline(aligned_audio_path)

    # Create output paths
    combined_speaker_path, transcription_path = create_output_paths(
        output_dir_path, speaker_audio_path
    )

    # Process segments and transcribe
    process_segments(
        segs_folder_path,
        combined_speaker_path,
        transcription_path,
        whisper_options=whisper_options,
    )

    return combined_speaker_path


def setup_directories(source_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    """Setup and clean output and workspace directories."""
    if output_dir.exists():
        shutil.rmtree(output_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    workspace_path = source_dir / "workspace"
    if workspace_path.exists():
        shutil.rmtree(workspace_path, ignore_errors=True)
    workspace_path.mkdir(parents=True, exist_ok=True)

    return output_dir, workspace_path


def get_audio_files(
    source_dir: Path, reference: str | bytes | os.PathLike[Any] | None = None
) -> tuple[Path, list[Path]]:
    """Get reference and speaker audio files from directory."""
    audio_file_paths = sorted(source_dir.glob("*.wav"))
    if not audio_file_paths:
        raise ValueError("No audio files found in the directory.")

    ref_path = to_path(reference) if reference else select_reference_audio(audio_file_paths)
    print(f"[INFO] Using reference audio: {ref_path}")

    speaker_files = [f for f in audio_file_paths if f != ref_path and "GMT" not in f.name]
    if not speaker_files:
        raise ValueError("No speaker audio files found in the directory.")

    return ref_path, speaker_files


def process_speaker_file(
    speaker_path: Path,
    reference_path: Path,
    workspace_path: Path,
    comp_duration: float,
    ss: float,
    out_duration: float,
) -> tuple[Path, SpeechTimeline]:
    """Process a single speaker file."""
    print(f"\033[92m[INFO] Processing file: {str(speaker_path)}\033[0m")

    # Align speaker audio to reference
    aligned_path = align_speaker_to_reference(
        reference_path,
        speaker_path,
        workspace_path,
        comp_duration=comp_duration,
    )

    # Prepare aligned audio
    aligned_path = prepare_audio_file(aligned_path, ss, out_duration)

    # Detect speech segments
    return detect_speech_timeline(aligned_path)


def preprocess_multi_files(
    reference: str | bytes | os.PathLike[Any] | None,
    source_dir: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
    ss: float = 0.0,
    out_duration: float = DEFAULT_OUT_AUDIO_DURATION,
    convert: bool = True,
) -> None:
    """Preprocess multiple audio files with improved organization."""
    source_dir_path = to_path(source_dir)
    output_dir_path = to_path(output_dir)

    # Setup directories
    output_dir_path, workspace_path = setup_directories(source_dir_path, output_dir_path)

    # Convert files if needed
    if convert:
        print("[INFO] Converting audio files to WAV format...")
        convert_all_files_to_wav(source_dir_path)

    # Get audio files
    reference_path, audio_file_paths = get_audio_files(source_dir_path, reference)

    # Process each speaker file
    with concurrent.futures.ThreadPoolExecutor() as executor:
        process_args = [
            (path, reference_path, workspace_path, comp_duration, ss, out_duration)
            for path in audio_file_paths
        ]
        results = list(executor.map(lambda args: process_speaker_file(*args), process_args))

    # Separate results
    segments_dir_list, timelines = zip(*results, strict=False)

    # Merge timelines and save audio
    merged_timeline = merge_timelines(list(timelines))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        save_args = [
            (audio_path, segments_dir, output_dir_path, merged_timeline)
            for audio_path, segments_dir in zip(audio_file_paths, segments_dir_list, strict=False)
        ]
        executor.map(
            lambda args: combine_segments_into_audio_with_timeline(
                args[1],  # segments_dir
                args[2] / f"{args[0].stem}.wav",  # target_audio_path
                args[3],  # merged_timeline
            ),
            save_args,
        )

    # Cleanup
    shutil.rmtree(workspace_path, ignore_errors=True)


def get_speaker_files(source_dir: Path) -> list[Path]:
    """Get speaker audio files from directory."""
    audio_files = [f for f in sorted(source_dir.glob("*.wav")) if "GMT" not in f.name]
    if not audio_files:
        raise ValueError("No audio files found in the directory.")
    return audio_files


def process_speaker_audio(
    audio_file_path: Path,
    output_dir: Path,
    whisper_options: str,
) -> None:
    """Process a single speaker's audio file."""
    # Copy and prepare audio file
    tmp_audio_file_path = output_dir / audio_file_path.name
    shutil.copy(audio_file_path, tmp_audio_file_path)

    # Detect speech segments
    segments_dir, _ = detect_speech_timeline(tmp_audio_file_path)

    # Create output paths and process segments
    speaker_name = audio_file_path.stem
    combined_speaker_path = output_dir / f"{speaker_name}.wav"
    transcription_path = output_dir / f"{speaker_name}.srt"

    process_segments(
        segments_dir,
        combined_speaker_path,
        transcription_path,
        whisper_options=whisper_options,
    )


def combine_outputs(
    output_dir: Path,
    audio_files: list[Path],
) -> None:
    """Combine individual outputs into final files."""
    # Combine transcriptions
    transcription_output_path = output_dir / "transcription.srt"
    combine_srt_files(output_dir, transcription_output_path)

    # Combine audio files
    audio_prefix = audio_files[0].stem
    if "-" in audio_prefix:
        audio_prefix = audio_prefix.split("-")[0]
    final_audio_path = output_dir / f"{audio_prefix}.wav"
    combine_audio_files(audio_files, final_audio_path)


def postprocess_multi_files(
    source_dir: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> None:
    """Postprocess multiple audio files with improved organization."""
    source_dir_path = to_path(source_dir)
    output_dir_path = to_path(output_dir)

    # Setup output directory
    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Get speaker files
    audio_file_paths = get_speaker_files(source_dir_path)

    # Process each speaker file
    with concurrent.futures.ThreadPoolExecutor() as executor:
        process_args = [(f, output_dir_path, whisper_options) for f in audio_file_paths]
        executor.map(lambda args: process_speaker_audio(*args), process_args)

    # Combine outputs into final files
    combine_outputs(output_dir_path, audio_file_paths)
