import concurrent.futures
import os
import shutil
from glob import glob

from waddle.audios.align_offset import align_speaker_to_reference
from waddle.audios.call_tools import convert_to_wav
from waddle.config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_OUT_AUDIO_DURATION
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


def select_reference_audio(audio_paths: list) -> str:
    """
    Automatically select a reference audio file starting with 'GMT'.

    Args:
        audio_paths (list): List of audio file paths.

    Returns:
        str: Path to the reference audio file.
    """
    gmt_files = [f for f in audio_paths if os.path.basename(f).startswith("GMT")]
    if not gmt_files:
        raise ValueError("No reference audio file found and no GMT file exists.")
    return gmt_files[0]


def process_single_file(
    aligned_audio_path: str,
    output_dir: str,
    speaker_file: str,
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

    segs_folder_path, _ = detect_speech_timeline(aligned_audio_path)

    # Transcribe segments and combine
    speaker_name = os.path.splitext(os.path.basename(speaker_file))[0]
    combined_speaker_path = os.path.join(output_dir, f"{speaker_name}.wav")
    transcription_path = os.path.join(output_dir, f"{speaker_name}.srt")
    process_segments(
        segs_folder_path,
        combined_speaker_path,
        transcription_path,
    )

    return combined_speaker_path


def preprocess_multi_files(
    reference_path: str | None,
    audio_source_directory: str | None,
    output_dir: str,
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
    ss: float = 0.0,
    out_duration: float = DEFAULT_OUT_AUDIO_DURATION,
    convert: bool = True,
) -> None:
    if audio_source_directory is not None and not os.path.exists(audio_source_directory):
        raise FileNotFoundError(f"Audio source directory not found: {audio_source_directory}")

    output_dir = os.path.abspath(output_dir)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)

    # Workspace for temporary files
    workspace = os.path.join(audio_source_directory, "workspace")
    # Recreate the workspace
    shutil.rmtree(workspace, ignore_errors=True)
    os.makedirs(workspace, exist_ok=True)

    # Convert to WAV files if the flag is set
    if convert:
        print("[INFO] Converting audio files to WAV format...")
        convert_to_wav(audio_source_directory)

    audio_files = sorted(glob(os.path.join(audio_source_directory, "*.wav")))
    if not audio_files:
        raise ValueError("No audio files found in the directory.")

    if reference_path is None:
        reference_path = select_reference_audio(audio_files)
    print(f"[INFO] Using reference audio: {reference_path}")

    audio_files = [f for f in audio_files if f != reference_path and "GMT" not in f]
    if not audio_files:
        raise ValueError("No speaker audio files found in the directory.")

    timelines: list[SpeechTimeline] = []
    segments_dir_list = []

    def process_file(speaker_file):
        print(f"\033[92m[INFO] Processing file: {speaker_file}\033[0m")

        # 1) Align each speaker audio to the reference
        aligned_audio_path = align_speaker_to_reference(
            reference_path,
            speaker_file,
            workspace,
            comp_duration=comp_duration,
        )

        # 2) Preprocess the aligned audio file
        segments_dir, timeline = detect_speech_timeline(aligned_audio_path)

        return segments_dir, timeline

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(process_file, audio_files))

    for segments_dir, timeline in results:
        segments_dir_list.append(segments_dir)
        timelines.append(timeline)

    merged_timeline = merge_timelines(timelines)

    def save_audio_with_timeline(audio_file_path, segments_dir):
        audio_file_name = os.path.splitext(os.path.basename(audio_file_path))[0]
        target_audio_path = os.path.join(output_dir, f"{audio_file_name}.wav")
        combine_segments_into_audio_with_timeline(
            segments_dir,
            target_audio_path,
            merged_timeline,
        )
        return target_audio_path

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(save_audio_with_timeline, audio_files, segments_dir_list)

    # Clean up workspace
    shutil.rmtree(workspace, ignore_errors=True)


def process_multi_files(
    reference_path: str,
    directory: str,
    output_path: str,
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
    out_duration: float = DEFAULT_OUT_AUDIO_DURATION,
    convert: bool = True,
) -> None:
    """
    Main pipeline:
      1) Auto-select or use given reference audio
      2) Align each speaker audio to reference
      3) Normalize, detect speech
      3.1)audacity
      3.2)detect speech, transcribe
      4) Combine final audios into one
      5) Combine final SRTs into one

    Args:
        reference_path (str): Path to the reference audio file (or None).
        directory (str): Directory containing .wav audio files.
        output_path (str): Output path for the combined audio (or None).
        comp_duration (float): Duration in seconds used for alignment comparison.
        out_duration (float): Duration in seconds for the output audio.
        convert (bool): Whether to convert all audio files to .wav format.
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    output_dir = os.path.join(directory, "out")
    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)

    # Convert to WAV files if the flag is set
    if convert:
        print("[INFO] Converting audio files to WAV format...")
        convert_to_wav(directory)

    audio_files = sorted(glob(os.path.join(directory, "*.wav")))
    if not audio_files:
        raise ValueError("No audio files found in the directory.")

    if reference_path is None:
        reference_path = select_reference_audio(audio_files)
    print(f"[INFO] Using reference audio: {reference_path}")

    audio_files = [f for f in audio_files if f != reference_path and "GMT" not in f]
    if not audio_files:
        raise ValueError("No speaker audio files found in the directory.")

    combined_speaker_paths = []

    for file_index, speaker_file in enumerate(audio_files):
        print(
            f"\033[92m[INFO] Processing file {file_index + 1} of "
            "{len(audio_files)}: {speaker_file}\033[0m"
        )

        # 1) Align each speaker audio to the reference
        aligned_audio_path = align_speaker_to_reference(
            reference_path,
            speaker_file,
            output_dir,
            comp_duration=comp_duration,
        )

        # 2) Process the aligned audio file
        combined_speaker_path = process_single_file(aligned_audio_path, output_dir, speaker_file)
        combined_speaker_paths.append(combined_speaker_path)

    audio_prefix = os.path.basename(audio_files[0]).split("-")[0]
    final_audio_path = output_path or os.path.join(output_dir, f"{audio_prefix}.wav")
    combine_audio_files(combined_speaker_paths, final_audio_path)

    combined_srt_path = os.path.join(output_dir, f"{audio_prefix}.srt")
    combine_srt_files(output_dir, combined_srt_path)

    print("[INFO] Final processing complete.")
