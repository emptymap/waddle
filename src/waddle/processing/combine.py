import os
import shutil
from glob import glob

from pydub import AudioSegment


def combine_segments_into_audio(
    segs_folder_path: str,
    combined_audio_path: str,
) -> None:
    """
    Combine segment files into a single audio, placing each at the correct offset.

    Args:
        segment_files (list): Paths to segment files.
        speech_segments (list): List of (start, end) tuples for each segment.
        output_audio_path (str): Where to save the combined audio file.
        total_duration (float): Total duration (in seconds) of the final audio.
    """
    segment_files = sorted(glob(os.path.join(segs_folder_path, "*.wav")))
    if not segment_files:
        print("\033[93m[WARNING] No segment files found for combining.\033[0m")

        # Output a dummy audio file
        final_audio = AudioSegment.silent(duration=10)
        final_audio.export(combined_audio_path, format="wav")

        # Clean up segs folder
        shutil.rmtree(segs_folder_path, ignore_errors=True)
        return
    end_mses = [
        int(os.path.basename(f).split("_")[2].split(".")[0]) for f in segment_files
    ]
    max_end_ms = max(end_mses)
    final_audio = AudioSegment.silent(duration=max_end_ms)

    for segment_file in segment_files:
        segment_audio = AudioSegment.from_file(segment_file)
        start_ms = int(os.path.basename(segment_file).split("_")[1].split(".")[0])
        final_audio = final_audio.overlay(segment_audio, position=start_ms)

    final_audio.export(combined_audio_path, format="wav")

    # Clean up segs folder
    shutil.rmtree(segs_folder_path, ignore_errors=True)


def combine_audio_files(aligned_audio_paths: list, output_audio_path: str) -> None:
    """
    Combine multiple aligned audio files by overlaying them sequentially.

    Args:
        aligned_audio_paths (list): Paths to aligned audio files.
        output_audio_path (str): Path to save the combined audio file.
    """
    combined_audio = None
    # Sort for making max duration audio
    aligned_audio_paths.sort(
        key=lambda x: AudioSegment.from_file(x).duration_seconds, reverse=True
    )
    for path in aligned_audio_paths:
        audio = AudioSegment.from_file(path)
        combined_audio = (
            audio if combined_audio is None else combined_audio.overlay(audio)
        )

    if combined_audio:
        combined_audio.export(output_audio_path, format="wav")


def parse_srt(file_path: str, speaker_name: str) -> list:
    """
    Parse an SRT file, attach speaker name to each text line,
    and return a list of (start_time_for_sorting, end_timestamp, text_with_speaker).

    Args:
        file_path (str): Path to the .srt file.
        speaker_name (str): Name of the speaker.

    Returns:
        list: List of tuples (start_time_for_sorting, end_timestamp, text_with_speaker).
    """
    entries = []
    with open(file_path, "r", encoding="utf-8") as f:
        blocks = f.read().strip().split("\n\n")
    os.remove(file_path)  # Cleanup after reading

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue

        timestamp = lines[1]
        start, end = timestamp.split(" --> ")
        text = " ".join(lines[2:])
        text_with_speaker = f"{speaker_name}: {text}"

        # Convert timestamps for sorting
        start_time_for_sorting = start.replace(",", ".")
        entries.append((start_time_for_sorting, end, text_with_speaker))
    return entries


def combine_srt_files(input_dir: str, output_file: str) -> None:
    """
    Combine all .srt files in a directory, add speaker names, and sort by timestamp.
    """

    srt_files = [f for f in os.listdir(input_dir) if f.endswith(".srt")]
    all_entries = []

    for srt_file in srt_files:
        if "-" in srt_file:
            speaker_name = os.path.basename(srt_file).split("-")[1].split(".")[0]
        else:
            speaker_name = os.path.basename(srt_file).split(".")[0]
        srt_path = os.path.join(input_dir, srt_file)
        all_entries.extend(parse_srt(srt_path, speaker_name))

    # Sort all entries by timestamp
    all_entries.sort(key=lambda x: x[0])

    # Write combined SRT file
    with open(output_file, "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(all_entries, start=1):
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
