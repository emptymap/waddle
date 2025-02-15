import concurrent.futures
import shutil
from pathlib import Path

from waddle.audios.align_offset import align_speaker_to_reference
from waddle.audios.call_tools import convert_to_wav
from waddle.audios.clip import clip_audio
from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_OUT_AUDIO_DURATION
from waddle.processing.combine import (
    combine_segments_into_audio_with_timeline,
    merge_timelines,
)
from waddle.processing.segment import (
    SpeechTimeline,
    detect_speech_timeline,
    process_segments,
)


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


def process_single_file(
    aligned_audio_path: Path,
    output_dir_path: Path,
    speaker_file: Path,
    ss: float = 0.0,
    out_duration: float | None = None,
) -> str:
    """
    Process a single audio file: normalize, detect speech, and transcribe.

    Args:
        aligned_audio_path (str): Path to the aligned audio file.
        output_dir (str): Output directory for processed files.
        speaker_file (str): Original speaker file name.

    Returns:
        str: Path to the combined speaker audio file.
    """
    clip_audio(aligned_audio_path, aligned_audio_path, ss=ss, out_duration=out_duration)

    segs_folder_path, _ = detect_speech_timeline(aligned_audio_path)

    # Transcribe segments and combine
    speaker_name = speaker_file.stem
    combined_speaker_path = output_dir_path / f"{speaker_name}.wav"
    transcription_path = output_dir_path / f"{speaker_name}.srt"
    process_segments(
        segs_folder_path,
        combined_speaker_path,
        transcription_path,
    )

    return combined_speaker_path


def preprocess_multi_files(
    reference_path_or_none: Path | None,
    source_dir_path: Path,
    output_dir_path: Path,
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
    ss: float = 0.0,
    out_duration: float = DEFAULT_OUT_AUDIO_DURATION,
    convert: bool = True,
) -> None:
    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Workspace for temporary files
    workspace = source_dir_path / "workspace" if source_dir_path is not None else None
    # Recreate the workspace
    shutil.rmtree(workspace, ignore_errors=True)
    workspace.mkdir(parents=True, exist_ok=True)

    # Convert to WAV files if the flag is set
    if convert:
        print("[INFO] Converting audio files to WAV format...")
        convert_to_wav(source_dir_path)

    audio_file_paths = sorted(source_dir_path.glob("*.wav"))
    if not audio_file_paths:
        raise ValueError("No audio files found in the directory.")

    reference_path = reference_path_or_none or select_reference_audio(audio_file_paths)
    print(f"[INFO] Using reference audio: {reference_path}")

    audio_file_paths = [f for f in audio_file_paths if f != reference_path and "GMT" not in f.name]
    if not audio_file_paths:
        raise ValueError("No speaker audio files found in the directory.")

    timelines: list[SpeechTimeline] = []
    segments_dir_list = []

    def process_file(speaker_file_path: Path):
        print(f"\033[92m[INFO] Processing file: {str(speaker_file_path)}\033[0m")

        # 1) Align each speaker audio to the reference
        aligned_audio_path = align_speaker_to_reference(
            reference_path,
            speaker_file_path,
            workspace,
            comp_duration=comp_duration,
        )
        clip_audio(aligned_audio_path, aligned_audio_path, ss=ss, out_duration=out_duration)

        # 2) Preprocess the aligned audio file
        segments_dir, timeline = detect_speech_timeline(aligned_audio_path)

        return segments_dir, timeline

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_file, audio_file_paths))

    for segments_dir, timeline in results:
        segments_dir_list.append(segments_dir)
        timelines.append(timeline)

    merged_timeline = merge_timelines(timelines)

    def save_audio_with_timeline(audio_file_path: Path, segments_dir):
        audio_file_name = Path(audio_file_path).stem
        target_audio_path = output_dir_path / f"{audio_file_name}.wav"
        combine_segments_into_audio_with_timeline(
            segments_dir,
            target_audio_path,
            merged_timeline,
        )
        return target_audio_path

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(save_audio_with_timeline, audio_file_paths, segments_dir_list)

    # Clean up workspace
    shutil.rmtree(workspace, ignore_errors=True)
