import shutil
from pathlib import Path
from typing import Optional, TypeAlias

from pydub import AudioSegment

from waddle.utils import parse_audio_filename

SpeechSegment: TypeAlias = tuple[int, int]
SpeechTimeline: TypeAlias = list[SpeechSegment]

SrtEntry: TypeAlias = tuple[str, str, str]
SrtEntries: TypeAlias = list[SrtEntry]


def get_segment_files(segs_folder_path: Path) -> list[Path]:
    """Get sorted list of WAV segment files."""
    return sorted(segs_folder_path.glob("*.wav"))


def create_empty_audio(duration_ms: int = 10) -> AudioSegment:
    """Create an empty audio segment of specified duration."""
    return AudioSegment.silent(duration=duration_ms)


def get_max_duration(seg_file_paths: list[Path]) -> int:
    """Get maximum duration from segment files."""
    end_mses = [parse_audio_filename(str(f))[1] for f in seg_file_paths]
    return max(end_mses) if end_mses else 10


def overlay_segments(base_audio: AudioSegment, seg_file_paths: list[Path]) -> AudioSegment:
    """Overlay audio segments onto base audio at correct positions."""
    final_audio = base_audio
    for seg_file_path in seg_file_paths:
        seg_audio = AudioSegment.from_file(str(seg_file_path))
        start_ms, _ = parse_audio_filename(str(seg_file_path))
        final_audio = final_audio.overlay(seg_audio, position=start_ms)
    return final_audio


def cleanup_segments_folder(segs_folder_path: Path) -> None:
    """Clean up segments folder after processing."""
    shutil.rmtree(segs_folder_path, ignore_errors=True)


def combine_segments_into_audio(
    segs_folder_path: Path,
    combined_audio_path: Path,
) -> None:
    """Combine segment files into a single audio, placing each at the correct offset."""
    # Get segment files
    seg_file_paths = get_segment_files(segs_folder_path)

    if not seg_file_paths:
        print("\033[93m[WARNING] No segment files found for combining.\033[0m")
        # Create and save empty audio
        empty_audio = create_empty_audio()
        empty_audio.export(combined_audio_path, format="wav")
    else:
        # Create base audio and overlay segments
        max_duration = get_max_duration(seg_file_paths)
        base_audio = create_empty_audio(max_duration)
        final_audio = overlay_segments(base_audio, seg_file_paths)
        final_audio.export(combined_audio_path, format="wav")

    # Cleanup
    cleanup_segments_folder(segs_folder_path)


def get_timeline_duration(timeline: SpeechTimeline) -> int:
    """Get maximum duration from timeline."""
    return adjust_pos_to_timeline(timeline, timeline[-1][1]) if timeline else 0


def overlay_segments_with_timeline(
    base_audio: AudioSegment, seg_file_paths: list[Path], timeline: SpeechTimeline
) -> AudioSegment:
    """Overlay audio segments onto base audio using timeline positions."""
    final_audio = base_audio
    for seg_file_path in seg_file_paths:
        seg_audio = AudioSegment.from_file(str(seg_file_path))
        start_ms, _ = parse_audio_filename(str(seg_file_path))
        position = adjust_pos_to_timeline(timeline, start_ms)
        final_audio = final_audio.overlay(seg_audio, position=position)
    return final_audio


def combine_segments_into_audio_with_timeline(
    segs_folder_path: Path,
    combined_audio_path: Path,
    timeline: SpeechTimeline,
) -> None:
    """Combine segment files into a single audio using timeline for positioning."""
    # Get segment files
    seg_file_paths = get_segment_files(segs_folder_path)

    # Get duration from timeline
    max_duration = get_timeline_duration(timeline)

    if not seg_file_paths:
        print("\033[93m[WARNING] No segment files found for combining.\033[0m")
        # Create and save empty audio
        empty_audio = create_empty_audio(max_duration)
        empty_audio.export(combined_audio_path, format="wav")
    else:
        # Create base audio and overlay segments using timeline
        base_audio = create_empty_audio(max_duration)
        final_audio = overlay_segments_with_timeline(base_audio, seg_file_paths, timeline)
        final_audio.export(str(combined_audio_path), format="wav")

    # Cleanup
    cleanup_segments_folder(segs_folder_path)


def adjust_pos_to_timeline(timeline: SpeechTimeline, pos: int) -> int:
    """
    Adjust the position in the original audio to an edited audio.
    This function converts a position in the original audio to the corresponding position
    in the edited audio, based on the provided timeline which specifies the valid audio
    segments and omits silence.

    Args:
        timeline (SpeechTimeline): A list of tuples where each tuple contains the start
                                   and end positions of valid audio segments.
        pos (int): The position in the original audio to be adjusted.
    Returns:
        int: The adjusted position in the edited audio.
    """

    running_total = 0
    for start, end in timeline:
        if pos <= start:
            # if `start_ms` is before this segment, it doesn't matter
            break
        if start < pos <= end:
            # `start_ms` is within this segment.
            # Add the valid time in this segment to `running_total` and return
            return running_total + (pos - start)
        # end < start_ms must hold
        # Add the length of this segment to `running_total`
        running_total += end - start
    return running_total


def sort_audio_paths_by_duration(audio_paths: list[Path]) -> list[Path]:
    """Sort audio paths by duration in descending order."""
    return sorted(
        audio_paths, key=lambda x: AudioSegment.from_file(x).duration_seconds, reverse=True
    )


def overlay_audio_files(audio_paths: list[Path]) -> AudioSegment:
    """Combine multiple audio files by overlaying them."""
    if not audio_paths:
        return create_empty_audio()

    base_audio = AudioSegment.from_file(str(audio_paths[0]))
    for path in audio_paths[1:]:
        audio = AudioSegment.from_file(str(path))
        base_audio = base_audio.overlay(audio)
    return base_audio


def combine_audio_files(aligned_audio_paths: list[Path], output_audio_path: Path) -> None:
    """Combine multiple aligned audio files by overlaying them sequentially."""
    # Sort paths by duration
    sorted_paths = sort_audio_paths_by_duration(aligned_audio_paths)

    # Combine audio files
    combined_audio = overlay_audio_files(sorted_paths)

    # Export result
    combined_audio.export(output_audio_path, format="wav")


def parse_srt(file_path: Path, speaker_name: Optional[str] = None) -> SrtEntries:
    """
    Parse an SRT file, attach speaker name to each text line,
    and return a list of (start_time_for_sorting, end_timestamp, text_with_speaker).

    Args:
        file_path (str): Path to the .srt file.
        speaker_name (str): Name of the speaker.

    Returns:
        list: List of tuples (start_time_for_sorting, end_timestamp, text_with_speaker).
    """
    entries: SrtEntries = []
    with open(str(file_path), "r", encoding="utf-8") as f:
        blocks = f.read().strip().split("\n\n")

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            continue

        timestamp = lines[1]
        start, end = timestamp.split(" --> ")
        text = " ".join(lines[2:])
        if speaker_name:
            text = f"{speaker_name}: {text}"

        # Convert timestamps for sorting
        start_time_for_sorting = start.replace(",", ".")
        end_time_for_sorting = end.replace(",", ".")
        entries.append((start_time_for_sorting, end_time_for_sorting, text))
    return entries


def get_speaker_name(file_path: Path) -> str:
    """Extract speaker name from file path."""
    name = file_path.stem
    if "-" in name:
        name = name.split("-")[1]
    return name


def process_srt_files(input_dir_path: Path) -> SrtEntries:
    """Process all SRT files in directory and return combined entries."""
    srt_file_paths = list(input_dir_path.glob("*.srt"))
    all_entries: SrtEntries = []

    for srt_file_path in srt_file_paths:
        speaker_name = get_speaker_name(srt_file_path)
        all_entries.extend(parse_srt(srt_file_path, speaker_name))
        srt_file_path.unlink()

    return sorted(all_entries, key=lambda x: x[0])


def write_srt_file(entries: SrtEntries, output_path: Path) -> None:
    """Write SRT entries to file."""
    with open(str(output_path), "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(entries, start=1):
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


def combine_srt_files(input_dir_path: Path, output_file_path: Path) -> None:
    """Combine all .srt files in a directory, add speaker names, and sort by timestamp."""
    # Process all SRT files
    all_entries = process_srt_files(input_dir_path)

    # Write combined output
    write_srt_file(all_entries, output_file_path)


def merge_timelines(timelines: list[SpeechTimeline]) -> SpeechTimeline:
    """
    Merges multiple speech timelines into a single, non-overlapping timeline.
    Args:
        timelines (list[SpeechTimeline]): A list of SpeechTimeline objects,
                                          where each SpeechTimeline is a list of tuples.
                                          Each tuple represents a segment with a start and end time.
    Returns:
        SpeechTimeline: A merged SpeechTimeline with non-overlapping segments,
                        sorted by start time.
    """

    all_segments: SpeechTimeline = []
    for timeline in timelines:
        all_segments.extend(timeline)

    # Sort and merge overlapping segments
    all_segments = list(set(all_segments))
    all_segments.sort(key=lambda x: x[0])

    merged: SpeechTimeline = []
    for seg in all_segments:
        # If merged is empty or current segment does not overlap the last one in merged
        if not merged or merged[-1][1] < seg[0]:
            merged.append(seg)
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], seg[1]))

    return merged
