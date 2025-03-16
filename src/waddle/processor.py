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
from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_LANGUAGE
from waddle.processing.combine import (
    combine_audio_files,
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


def process_single_file(
    aligned_audio: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    speaker_audio: str | bytes | os.PathLike[Any],
    ss: float = 0.0,
    out_duration: float | None = None,
    no_noise_remove: bool = False,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> Path:
    """
    Process a single audio file: normalize, detect speech, and transcribe.

    Args:
        aligned_audio (str | os.PathLike): Path to the aligned audio file.
        output_dir (str | os.PathLike): Path to the output directory.
        speaker_audio (str | os.PathLike): Path to the speaker audio file.
        ss (float, optional): Start time offset in seconds. Defaults to 0.0.
        out_duration (float | None, optional): Duration of the processed output audio in seconds.

    Returns:
        Path: Path to the combined speaker audio file.
    """
    aligned_audio_path = to_path(aligned_audio)
    output_dir_path = to_path(output_dir)
    speaker_audio_path = to_path(speaker_audio)

    if aligned_audio_path.suffix != ".wav":
        convert_to_wav(aligned_audio_path)
        aligned_audio_path = aligned_audio_path.with_suffix(".wav")
    if ss > 0 or out_duration:
        clip_audio(aligned_audio_path, aligned_audio_path, ss=ss, out_duration=out_duration)
    if not no_noise_remove:
        remove_noise(aligned_audio_path, aligned_audio_path)

    segs_folder_path, _ = detect_speech_timeline(aligned_audio_path)

    # Transcribe segments and combine
    speaker_name = speaker_audio_path.stem
    combined_speaker_path = output_dir_path / f"{speaker_name}.wav"
    transcription_path = output_dir_path / f"{speaker_name}.srt"
    process_segments(
        segs_folder_path,
        combined_speaker_path,
        transcription_path=transcription_path,
        whisper_options=whisper_options,
    )

    return combined_speaker_path


def preprocess_multi_files(
    reference: str | bytes | os.PathLike[Any] | None,
    source_dir: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
    ss: float = 0.0,
    out_duration: float | None = None,
    no_noise_remove: bool = False,
    convert: bool = True,
    transcribe: bool = False,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> None:
    source_dir_path = to_path(source_dir)
    output_dir_path = to_path(output_dir)

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    # Workspace for temporary files
    workspace_path = source_dir_path / "workspace"
    if workspace_path.exists():
        shutil.rmtree(workspace_path, ignore_errors=True)
    workspace_path.mkdir(parents=True, exist_ok=True)

    # Convert to WAV files if the flag is set
    if convert:
        print("[INFO] Converting audio files to WAV format...")
        convert_all_files_to_wav(source_dir_path)

    audio_file_paths = sorted(source_dir_path.glob("*.wav"))
    if not audio_file_paths:
        raise ValueError("No audio files found in the directory.")

    reference_path = to_path(reference) if reference else select_reference_audio(audio_file_paths)
    print(f"[INFO] Using reference audio: {reference_path}")

    audio_file_paths = [f for f in audio_file_paths if f != reference_path and "GMT" not in f.name]
    if not audio_file_paths:
        raise ValueError("No speaker audio files found in the directory.")

    timelines: list[SpeechTimeline] = []
    segments_dir_list = []

    def process_file(speaker_audio_path: Path):
        print(f"\033[92m[INFO] Processing file: {str(speaker_audio_path)}\033[0m")

        # 1) Align each speaker audio to the reference
        aligned_audio_path = align_speaker_to_reference(
            reference_path,
            speaker_audio_path,
            workspace_path,
            comp_duration=comp_duration,
        )
        clip_audio(aligned_audio_path, aligned_audio_path, ss=ss, out_duration=out_duration)
        if not no_noise_remove:
            remove_noise(aligned_audio_path, aligned_audio_path)

        # 2) Preprocess the aligned audio file
        segments_dir, timeline = detect_speech_timeline(aligned_audio_path)

        return segments_dir, timeline

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_file, audio_file_paths))

    for segments_dir, timeline in results:
        segments_dir_list.append(segments_dir)
        timelines.append(timeline)

    merged_timeline = merge_timelines(timelines)

    for audio_file_path, segments_dir in zip(audio_file_paths, segments_dir_list, strict=False):
        speaker_name = audio_file_path.stem
        combined_speaker_path = output_dir_path / f"{speaker_name}.wav"
        # If transcribe is False, transcription_path is None and not transcribed.
        transcription_path = output_dir_path / f"{speaker_name}.srt" if transcribe else None
        process_segments(
            segments_dir,
            combined_speaker_path,
            transcription_path=transcription_path,
            whisper_options=whisper_options,
            timeline=merged_timeline,
        )

    # Clean up workspace_path
    shutil.rmtree(workspace_path, ignore_errors=True)

    if not transcribe:
        return

    audio_prefix = audio_file_paths[0].stem
    if "-" in audio_prefix:
        audio_prefix = audio_prefix.split("-")[0]
    transcription_output_path = output_dir_path / f"{audio_prefix}.srt"
    combine_srt_files(output_dir_path, transcription_output_path)


def postprocess_multi_files(
    source_dir: str | bytes | os.PathLike[Any],
    output_dir: str | bytes | os.PathLike[Any],
    ss: float = 0.0,
    out_duration: float | None = None,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> None:
    source_dir_path = to_path(source_dir)
    output_dir_path = to_path(output_dir)

    audio_file_paths = [f for f in sorted(source_dir_path.glob("*.wav")) if "GMT" not in f.name]
    if not audio_file_paths:
        raise ValueError("No audio files found in the directory.")

    if output_dir_path.exists():
        shutil.rmtree(output_dir_path, ignore_errors=True)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    for audio_file_path in audio_file_paths:
        tmp_audio_file_path = output_dir_path / audio_file_path.name
        if ss > 0 or out_duration:
            clip_audio(audio_file_path, tmp_audio_file_path, ss=ss, out_duration=out_duration)
        else:
            shutil.copy(audio_file_path, tmp_audio_file_path)
        segments_dir, _ = detect_speech_timeline(tmp_audio_file_path)
        speaker_name = audio_file_path.stem
        combined_speaker_path = output_dir_path / f"{speaker_name}.wav"
        transcription_path = output_dir_path / f"{speaker_name}.srt"
        process_segments(
            segments_dir,
            combined_speaker_path,
            transcription_path=transcription_path,
            whisper_options=whisper_options,
        )

    audio_prefix = audio_file_paths[0].stem
    if "-" in audio_prefix:
        audio_prefix = audio_prefix.split("-")[0]

    transcription_output_path = output_dir_path / f"{audio_prefix}.srt"
    combine_srt_files(output_dir_path, transcription_output_path)
    shutil.copy(transcription_output_path, output_dir_path / f"{audio_prefix}.md")

    final_audio_path = output_dir_path / f"{audio_prefix}.wav"
    combined_audio_paths = sorted(output_dir_path.glob("*.wav"))
    combine_audio_files(combined_audio_paths, final_audio_path)
