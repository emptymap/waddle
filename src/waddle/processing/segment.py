import shutil
from pathlib import Path

import numpy as np
from pydub import AudioSegment
from tqdm import tqdm

from waddle.audios.call_tools import transcribe
from waddle.config import (
    DEFAULT_BUFFER_DURATION,
    DEFAULT_CHUNK_DURATION,
    DEFAULT_LANGUAGE,
    DEFAULT_TARGET_DB,
    DEFAULT_THRESHOLD_DB,
)
from waddle.processing.combine import SpeechTimeline, combine_segments_into_audio
from waddle.utils import format_audio_filename, format_time, parse_audio_filename, time_to_seconds


def find_speech_segments(
    audio: AudioSegment,
    threshold_db: float = DEFAULT_THRESHOLD_DB,
    chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
    buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
) -> SpeechTimeline:
    """Find speech segments in audio based on loudness threshold."""
    segments = []
    current_segment = None
    duration = len(audio)

    for i in tqdm(
        range(0, duration, chunk_size_ms),
        desc="[INFO] Detecting speech segments",
    ):
        end = min(i + chunk_size_ms, duration)
        # Extract segment using pydub's built-in method
        chunk = audio[i:end]
        if not isinstance(chunk, AudioSegment):
            chunk = AudioSegment.silent(duration=0)
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

    if current_segment is not None:
        segments.append((current_segment[0], current_segment[1]))

    return merge_segments(segments)


def calculate_normalization(
    audio: AudioSegment,
    segments: SpeechTimeline,
    target_dBFS: float = DEFAULT_TARGET_DB,
) -> float:
    """Calculate gain adjustment for audio normalization."""
    if not segments:
        return 0.0

    max_dBFS_list = []
    for seg in segments:
        # Extract segment using pydub's built-in method
        segment = audio[seg[0] : seg[1]]
        if not isinstance(segment, AudioSegment):
            continue
        max_dBFS_list.append(segment.dBFS)
    max_dBFS_95th_percentile = float(np.percentile(max_dBFS_list, 95))
    return target_dBFS - max_dBFS_95th_percentile


def save_normalized_segments(
    audio: AudioSegment,
    segments: SpeechTimeline,
    output_dir: Path,
    gain_adjustment: float,
) -> None:
    """Save normalized audio segments to files."""
    for seg in segments:
        # Extract segment using pydub's built-in method
        segment = audio[seg[0] : seg[1]]
        if not isinstance(segment, AudioSegment):
            continue
        normalized_audio = segment.apply_gain(gain_adjustment)
        seg_audio_path = output_dir / format_audio_filename("seg", seg[0], seg[1])
        normalized_audio.export(seg_audio_path, format="wav")


def setup_segments_directory(audio_path: Path) -> Path:
    """Setup and return directory for storing segments."""
    segs_folder_path = audio_path.parent / f"{audio_path.stem}_segs"
    if segs_folder_path.exists():
        shutil.rmtree(segs_folder_path)
    segs_folder_path.mkdir(parents=True, exist_ok=True)
    return segs_folder_path


def detect_speech_timeline(
    audio_path: Path,
    threshold_db: float = DEFAULT_THRESHOLD_DB,
    chunk_size_ms: int = int(DEFAULT_CHUNK_DURATION * 1000),
    buffer_size_ms: int = int(DEFAULT_BUFFER_DURATION * 1000),
    target_dBFS: float = DEFAULT_TARGET_DB,
) -> tuple[Path, SpeechTimeline]:
    """
    Detects and processes speech segments in an audio file.

    This function coordinates the speech detection process:
    1. Loads the audio file
    2. Detects speech segments based on loudness
    3. Normalizes the audio segments
    4. Saves the processed segments to disk

    Returns the path to the segments directory and the timeline of segments.
    """
    # Load audio
    audio = AudioSegment.from_file(str(audio_path))

    # Find speech segments
    segments = find_speech_segments(
        audio,
        threshold_db,
        chunk_size_ms,
        buffer_size_ms,
    )

    if not segments:
        print("[Warning] No speech segments detected.")
        segs_folder_path = setup_segments_directory(audio_path)
        return segs_folder_path, []

    # Calculate normalization
    gain_adjustment = calculate_normalization(audio, segments, target_dBFS)
    print(f"[INFO] Global normalization applied with gain adjustment: {gain_adjustment} dB")

    # Setup output directory and save segments
    segs_folder_path = setup_segments_directory(audio_path)
    save_normalized_segments(audio, segments, segs_folder_path, gain_adjustment)

    # Cleanup
    audio_path.unlink()

    return segs_folder_path, segments


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


def transcribe_segments(
    segs_folder_path: Path,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> list[tuple[str, str, str]]:
    """Transcribe audio segments and return entries with adjusted timestamps."""
    transcription_entries = []
    segs_file_paths = sorted(segs_folder_path.glob("*.wav"))

    for segs_file_path in tqdm(
        segs_file_paths,
        desc=f"[INFO] Transcribing {len(segs_file_paths)} segments",
        total=len(segs_file_paths),
        dynamic_ncols=True,
        bar_format="{l_bar}{bar:50}{r_bar}",
    ):
        start, _ = parse_audio_filename(str(segs_file_path))
        start_seconds = float(start) / 1000

        # Transcribe segment
        srt_output_path = Path(segs_file_path).with_suffix(".srt")
        transcribe(segs_file_path, srt_output_path, options=whisper_options)

        # Process transcription and cleanup
        process_segment_transcription(srt_output_path, start_seconds, transcription_entries)
        srt_output_path.unlink()

    return transcription_entries


def save_transcription_file(
    entries: list[tuple[str, str, str]],
    output_path: Path,
) -> None:
    """Save transcription entries to an SRT file."""
    with open(str(output_path), "w", encoding="utf-8") as srt_out:
        for idx, (start_time, end_time, text) in enumerate(entries, start=1):
            srt_out.write(f"{idx}\n")
            srt_out.write(f"{start_time} --> {end_time}\n")
            srt_out.write(f"{text}\n\n")


def process_segments(
    segs_folder_path: Path,
    combined_audio_path: Path,
    transcription_output_path: Path,
    whisper_options: str = f"-l {DEFAULT_LANGUAGE}",
) -> None:
    """
    Process speech segments: transcribe and combine into final outputs.

    This function coordinates the segment processing:
    1. Transcribes each audio segment
    2. Combines transcriptions into a single SRT file
    3. Combines audio segments into a single audio file
    """
    # Transcribe segments
    transcription_entries = transcribe_segments(segs_folder_path, whisper_options)

    # Save combined transcription
    save_transcription_file(transcription_entries, transcription_output_path)

    # Combine audio segments
    combine_segments_into_audio(segs_folder_path, combined_audio_path)


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
