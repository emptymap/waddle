import os
import shutil
from glob import glob

import numpy as np
from pydub import AudioSegment
from tqdm import tqdm

from waddle.audios.call_tools import remove_noise, transcribe
from waddle.config import (
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHUNK_DURATION,
    DEFAULT_TARGET_DB,
    DEFAULT_THRESHOLD_DB,
)
from waddle.processing.combine import SpeechTimeline, combine_segments_into_audio
from waddle.utils import format_audio_filename, format_time, parse_audio_filename, time_to_seconds


def detect_speech_timeline(
    audio_path: str,
    threshold_db: float = DEFAULT_THRESHOLD_DB,
    chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
    buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
    target_dBFS: float = DEFAULT_TARGET_DB,
) -> tuple[str, SpeechTimeline]:
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
    audio = AudioSegment.from_file(audio_path)

    segments = []
    current_segment = None

    # Create a clean 'chunks' folder
    identifier = os.path.splitext(os.path.basename(audio_path))[0]
    chunks_folder = os.path.join(os.path.dirname(audio_path), "chunks", identifier)
    if os.path.exists(chunks_folder):
        shutil.rmtree(chunks_folder)
    os.makedirs(chunks_folder)

    duration = len(audio)
    for i in tqdm(
        range(0, duration, chunk_size_ms),
        desc="[INFO] Detecting speech segments",
    ):
        chunk = audio[i : i + chunk_size_ms]
        if not chunk.dBFS > threshold_db:
            if current_segment is not None:
                segments.append((current_segment[0], current_segment[1]))
                current_segment = None
            continue

        temp_chunk_path = os.path.join(
            chunks_folder, format_audio_filename("chunk", i, i + chunk_size_ms)
        )
        chunk.export(temp_chunk_path, format="wav")
        remove_noise(temp_chunk_path, temp_chunk_path)
        chunk = AudioSegment.from_file(temp_chunk_path)

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
    audio_file_name = os.path.splitext(os.path.basename(audio_path))[0]
    segs_folder_path = os.path.join(os.path.dirname(audio_path), f"{audio_file_name}_segs")
    if os.path.exists(segs_folder_path):
        shutil.rmtree(segs_folder_path)
    os.makedirs(segs_folder_path)

    # collect max_dBFS for each segment
    max_dBFS_list = []
    for seg in merged_segments:
        seg_audio = audio[seg[0] : seg[1]]
        max_dBFS_list.append(seg_audio.dBFS)

    # calculate 95th percentile of max_dBFS
    max_dBFS_95th_percentile = np.percentile(max_dBFS_list, 95)

    # Calculate gain adjustment to achieve target_dBFS for 95th percentile
    gain_adjustment = target_dBFS - max_dBFS_95th_percentile

    # Apply normalization to all segments
    for seg in merged_segments:
        seg_audio = audio[seg[0] : seg[1]]
        normalized_audio = seg_audio.apply_gain(gain_adjustment)
        seg_audio_path = os.path.join(
            segs_folder_path, format_audio_filename("seg", seg[0], seg[1])
        )
        normalized_audio.export(seg_audio_path, format="wav")
        # Remove_noise is called twice, but this is done because accuracy is poor
        # if it is not written for each sentence.
        remove_noise(seg_audio_path, seg_audio_path)

    # Clean up audio
    os.remove(audio_path)

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
    segs_folder_path: str,
    combined_audio_path: str,
    transcription_output_path: str,
    language: str = "ja",
) -> None:
    """
    Transcribe only the detected speech segments, adjust timestamps,
    and combine them into a single audio file.

    Args:
        segs_folder_path (str): Path to the folder containing the speech segments.
        combined_audio_path (str): Path to save the combined audio file.
        transcription_output_path (str): Path to save the combined transcription file.
        language (str): Language code for transcription.
    """
    segs_file_paths = sorted(glob(os.path.join(segs_folder_path, "*.wav")))
    transcription_entries = []

    for segs_file_path in tqdm(
        segs_file_paths,
        desc=f"[INFO] Transcribing {len(segs_file_paths)} segments",
        total=len(segs_file_paths),
        dynamic_ncols=True,
        bar_format="{l_bar}{bar:50}{r_bar}",
    ):
        start, _ = parse_audio_filename(segs_file_path)
        start_seconds = float(start) / 1000

        # Transcribe segment
        srt_output_path = f"{os.path.splitext(segs_file_path)[0]}.srt"
        transcribe(segs_file_path, srt_output_path, language=language)

        # Adjust transcription timestamps
        process_segment_transcription(srt_output_path, start_seconds, transcription_entries)
        os.remove(srt_output_path)

    # Create a single SRT file from all segments
    with open(transcription_output_path, "w", encoding="utf-8") as srt_out:
        for idx, (start_time, end_time, text) in enumerate(transcription_entries, start=1):
            srt_out.write(f"{idx}\n")
            srt_out.write(f"{start_time} --> {end_time}\n")
            srt_out.write(f"{text}\n\n")

    # Combine segments into one audio file
    combine_segments_into_audio(
        segs_folder_path,
        combined_audio_path,
    )


def process_segment_transcription(
    transcribe_file_path: str, start_offset: float, transcription_entries: list
) -> None:
    """
    Adjust timestamps in a segment's transcription file by adding the start offset,
    then append entries to the shared list.

    Args:
        transcribe_file_path (str): Path to the .srt transcription file.
        start_offset (float): Offset in seconds to add to each timestamp.
        transcription_entries (list): Output list for adjusted transcription entries.
    """
    if not os.path.isfile(transcribe_file_path):
        print(f"[Warning] SRT file not found for segment: {transcribe_file_path}")
        return

    with open(transcribe_file_path, "r", encoding="utf-8") as srt_file:
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
