import os
import shutil
from glob import glob

from .audios.align_offset import align_speaker_to_reference
from .audios.call_tools import convert_to_wav
from .audios.effects import normalize_audio
from .config import DEFAULT_COMP_AUDIO_DURATION, DEFAULT_OUT_AUDIO_DURATION
from .processing.combine import combine_audio_files, combine_srt_files
from .processing.segment import detect_speech_segments, process_segments


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
      3) Normalize, detect speech, transcribe
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
    print(f"[INFO] Found {len(audio_files)} speaker audio files.")

    combined_speaker_paths = []

    for file_index, speaker_file in enumerate(audio_files):
        # 1) Align each speaker audio to the reference
        print(f"{file_index + 1}/{len(audio_files)}, Step 1: Aligning {speaker_file}")
        aligned_audio_path = align_speaker_to_reference(
            reference_path,
            speaker_file,
            output_dir,
            comp_duration=comp_duration,
            out_duration=out_duration,
        )

        # 2) Normalize, detect speech, transcribe
        print(
            f"{file_index + 1}/{len(audio_files)}, Step 2: Normalizing {aligned_audio_path}"
        )
        normalize_audio(aligned_audio_path, aligned_audio_path)

        # 3) Detect speech segments
        print(
            f"{file_index + 1}/{len(audio_files)}, Step 3: Detecting speech {aligned_audio_path}"
        )
        detect_speech_segments(aligned_audio_path)

        # 4) Transcribe segments
        print(
            f"{file_index + 1}/{len(audio_files)}, Step 4: Transcribing {aligned_audio_path}"
        )
        speaker_name = os.path.splitext(os.path.basename(speaker_file))[0]
        segs_folder_path = os.path.join(output_dir, "segs")
        combined_speaker_path = os.path.join(output_dir, f"{speaker_name}.wav")
        transcription_path = os.path.join(output_dir, f"{speaker_name}.srt")
        process_segments(
            segs_folder_path,
            combined_speaker_path,
            transcription_path,
        )

        # Save the combined speaker audio path
        combined_speaker_paths.append(combined_speaker_path)

    audio_prefix = os.path.basename(audio_files[0]).split("-")[0]
    final_audio_path = output_path or os.path.join(output_dir, f"{audio_prefix}.wav")
    combine_audio_files(combined_speaker_paths, final_audio_path)

    combined_srt_path = os.path.join(output_dir, f"{audio_prefix}.srt")
    combine_srt_files(output_dir, combined_srt_path)

    print("[INFO] Final processing complete.")
