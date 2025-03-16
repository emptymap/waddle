import shutil
from pathlib import Path

import numpy as np
from pydub import AudioSegment
from tqdm import tqdm

from waddle.audios.call_tools import transcribe_in_batches
from waddle.config import (
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHUNK_DURATION,
    DEFAULT_LANGUAGE,
    DEFAULT_TARGET_DB,
    DEFAULT_THRESHOLD_DB,
)
from waddle.processing.combine import SpeechTimeline, combine_segments_into_audio
from waddle.utils import format_audio_filename, format_time, parse_audio_filename, time_to_seconds


def detect_speech_timeline(
    audio_path: Path,
    threshold_db: float = DEFAULT_THRESHOLD_DB,
    chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
    buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
    target_dBFS: float = DEFAULT_TARGET_DB,
) -> tuple[Path, SpeechTimeline]:
    """
    Detects speech segments in an audio file based on a specified loudness threshold.
    Each detected segment includes a buffer of audio before and after to ensure completeness.
    The detected segments are normalized to achieve a global mean dBFS of target_dBFS.

    Args:
        audio_path (str): Path to the input audio file.
        threshold_db (float): Loudness threshold in dBFS for detecting speech.
        chunk_size_ms (int): Duration of each audio chunk in milliseconds.
        buffer_size_ms (int): Additional buffer duration in milliseconds for segment merging.
        target_dBFS (float): Target loudness level (dBFS) for normalized audio segments.
        out_duration (float, optional): Maximum duration of the processed output audio in seconds.

    Returns
        segs_folder_path (str): Path to the directory containing the extracted speech segments.
        merged_segments (SpeechTimeline): List of detected and merged speech segments.
    """
    audio = AudioSegment.from_file(str(audio_path))

    segments = []
    current_segment = None

    # Create a clean 'chunks' folder
    identifier = audio_path.stem
    chunks_folder = audio_path.parent / "chunks" / identifier
    if chunks_folder.exists():
        shutil.rmtree(chunks_folder)
    chunks_folder.mkdir(parents=True, exist_ok=True)

    duration = len(audio)
    for i in tqdm(
        range(0, duration, chunk_size_ms),
        desc="[INFO] Detecting speech segments",
    ):
        chunk = audio[i : i + chunk_size_ms]
        if chunk.dBFS > threshold_db:
            start_ms = max(0, i - buffer_size_ms)
            end_ms = min(duration, i + chunk_size_ms + buffer_size_ms)
            if current_segment is None:
                current_segment = [start_ms, end_ms]
            else:
                current_segment[1] = end_ms
        else:
            if current_segment is not None:
                segments.append((current_segment[0], current_segment[1]))
                current_segment = None

    # Finalize last segment if any
    if current_segment is not None:
        segments.append((current_segment[0], current_segment[1]))

    # Clean up chunks
    shutil.rmtree(chunks_folder)

    # Merge overlapping/adjacent segments
    merged_segments = merge_segments(segments)

    # Save segment to disk
    audio_file_name = audio_path.stem
    segs_folder_path = audio_path.parent / f"{audio_file_name}_segs"
    if segs_folder_path.exists():
        shutil.rmtree(segs_folder_path)
    segs_folder_path.mkdir(parents=True, exist_ok=True)

    # collect max_dBFS for each segment
    max_dBFS_list = []
    for seg in merged_segments:
        seg_audio = audio[seg[0] : seg[1]]
        max_dBFS_list.append(seg_audio.dBFS)

    # calculate 95th percentile of max_dBFS
    if not max_dBFS_list:
        print("[Warning] No speech segments detected.")
        return segs_folder_path, []
    max_dBFS_95th_percentile = np.percentile(max_dBFS_list, 95)

    # Calculate gain adjustment to achieve target_dBFS for 95th percentile
    gain_adjustment = target_dBFS - max_dBFS_95th_percentile

    # Apply normalization to all segments
    for seg in merged_segments:
        seg_audio = audio[seg[0] : seg[1]]
        normalized_audio = seg_audio.apply_gain(gain_adjustment)
        seg_audio_path = segs_folder_path / format_audio_filename("seg", seg[0], seg[1])
        normalized_audio.export(seg_audio_path, format="wav")

    # Clean up audio
    audio_path.unlink()

    print(f"[INFO] Global normalization applied with gain adjustment: {gain_adjustment} dB")

    return segs_folder_path, merged_segments


def merge_segments(segments: SpeechTimeline) -> SpeechTimeline:
    merged_segments = []
    for seg in segments:
        if not merged_segments or seg[0] > merged_segments[-1][1]:
            merged_segments.append(seg)
        else:
            merged_segments[-1] = (
                merged_segments[-1][0],
                max(merged_segments[-1][1], seg[1]),
            )
    return merged_segments


def process_segments(
    segs_folder_path: Path,
    combined_audio_path: Path,
    transcription_path: Path | None = None,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
    timeline: SpeechTimeline | None = None,
) -> None:
    """
    Transcribe only the detected speech segments, adjust timestamps,
    and combine them into a single audio file.

    Args:
        segs_folder_path (str): Path to the folder containing the speech segments.
        combined_audio_path (str): Path to save the combined audio file.
        transcription_path (str): Path to save the combined transcription file.
        language (str): Language code for transcription.
    """
    seg_file_paths = sorted(segs_folder_path.glob("*.wav"), key=lambda x: int(x.stem.split("_")[1]))
    transcription_entries = []

    if transcription_path:
        input_output_paths = []
        for segs_file_path in seg_file_paths:
            # Transcribe segment
            srt_output_path = Path(segs_file_path).with_suffix(".srt")
            input_output_paths.append((segs_file_path, srt_output_path))

        transcribe_in_batches(input_output_paths, options=whisper_options)

        for segs_file_path, srt_output_path in input_output_paths:
            start, _ = parse_audio_filename(str(segs_file_path))
            start_seconds = float(start) / 1000

            # Adjust transcription timestamps
            process_segment_transcription(
                segs_file_path.with_suffix(".srt"), start_seconds, transcription_entries
            )
            srt_output_path.unlink()

        # Create a single SRT file from all segments
        with open(str(transcription_path), "w", encoding="utf-8") as srt_out:
            for idx, (start_time, end_time, text) in enumerate(transcription_entries, start=1):
                srt_out.write(f"{idx}\n")
                srt_out.write(f"{start_time} --> {end_time}\n")
                srt_out.write(f"{text}\n\n")

    # Combine segments into one audio file
    combine_segments_into_audio(
        segs_folder_path,
        combined_audio_path,
        timeline=timeline,
    )


def process_segment_transcription(
    transcribe_file_path: Path, start_offset: float, transcription_entries: list
) -> None:
    """
    Adjust timestamps in a segment's transcription file by adding the start offset,
    then append entries to the shared list.

    Args:
        transcribe_file_path (str): Path to the .srt transcription file.
        start_offset (float): Offset in seconds to add to each timestamp.
        transcription_entries (list): Output list for adjusted transcription entries.
    """
    transcribe_file_path = Path(
        transcribe_file_path
    )  # TODO: Delete it after switch to Pathlib in test
    if not transcribe_file_path.is_file():
        print(f"[Warning] SRT file not found for segment: {transcribe_file_path}")
        return

    with open(str(transcribe_file_path), "r", encoding="utf-8") as srt_file:
        blocks = srt_file.read().strip().split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue

        # Extract timestamps and text
        _, timestamps, *text_lines = lines
        s_timestamp, e_timestamp = timestamps.split(" --> ")
        text = " ".join(text_lines)

        # Adjust timestamps
        adjusted_start = format_time(start_offset + time_to_seconds(s_timestamp))
        adjusted_end = format_time(start_offset + time_to_seconds(e_timestamp))

        transcription_entries.append((adjusted_start, adjusted_end, text))
