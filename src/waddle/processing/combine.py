import shutil
from pathlib import Path
from typing import Optional, TypeAlias

from pydub import AudioSegment

from waddle.utils import parse_audio_filename

SpeechSegment: TypeAlias = tuple[int, int]
SpeechTimeline: TypeAlias = list[SpeechSegment]

SrtEntry: TypeAlias = tuple[str, str, str]
SrtEntries: TypeAlias = list[SrtEntry]


def combine_segments_into_audio(
    segs_folder_path: Path,
    combined_audio_path: Path,
    timeline: SpeechTimeline | None = None,
) -> None:
    segs_folder_path = Path(segs_folder_path)  # TODO: Delete it after switch to Pathlib in test
    combined_audio_path = Path(
        combined_audio_path
    )  # TODO: Delete it after switch to Pathlib in test

    seg_file_paths = sorted(segs_folder_path.glob("*.wav"), key=lambda x: int(x.stem.split("_")[1]))
    max_end_ms = adjust_pos_to_timeline(timeline, timeline[-1][1]) if timeline else 1
    if not seg_file_paths:
        print("\033[93m[WARNING] No segment files found for combining.\033[0m")

        # Output a dummy audio file
        final_audio = AudioSegment.silent(duration=max_end_ms)
        final_audio.export(combined_audio_path, format="wav")

        # Clean up segs folder
        shutil.rmtree(segs_folder_path, ignore_errors=True)
        return

    if not timeline:
        _, end_ms = parse_audio_filename(str(seg_file_paths[-1]))
        timeline = [(0, end_ms)]
        max_end_ms = end_ms

    final_audio = AudioSegment.silent(duration=max_end_ms)

    for seg_file_path in seg_file_paths:
        seg_audio = AudioSegment.from_file(str(seg_file_path))
        start_ms, _ = parse_audio_filename(str(seg_file_path))
        final_audio = final_audio.overlay(
            seg_audio, position=adjust_pos_to_timeline(timeline, start_ms)
        )

    final_audio.export(str(combined_audio_path), format="wav")


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


def combine_audio_files(aligned_audio_paths: list[Path], output_audio_path: Path) -> None:
    """
    Combine multiple aligned audio files by overlaying them sequentially.

    Args:
        aligned_audio_paths (list): Paths to aligned audio files.
        output_audio_path (str): Path to save the combined audio file.
    """
    combined_audio = None
    # Sort for making max duration audio
    aligned_audio_paths.sort(key=lambda x: AudioSegment.from_file(x).duration_seconds, reverse=True)
    for path in aligned_audio_paths:
        audio = AudioSegment.from_file(str(path))
        combined_audio = audio if combined_audio is None else combined_audio.overlay(audio)

    if combined_audio:
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


def combine_srt_files(input_dir_path: Path, output_file_path: Path) -> None:
    """
    Combine all .srt files in a directory, add speaker names, and sort by timestamp.
    """
    input_dir_path = Path(input_dir_path)  # TODO: Delete it after switch to Pathlib in test
    output_file_path = Path(output_file_path)  # TODO: Delete it after switch to Pathlib in test
    srt_file_paths = [f for f in input_dir_path.glob("*.srt")]
    all_entries: SrtEntries = []

    for srt_file_path in srt_file_paths:
        srt_file_name = srt_file_path.stem
        if "-" in srt_file_name:
            srt_file_name = srt_file_name.split("-")[1]
        all_entries.extend(parse_srt(srt_file_path, srt_file_name))
        srt_file_path.unlink()

    # Sort all entries by timestamp
    all_entries.sort(key=lambda x: x[0])

    # Write combined SRT file
    with open(str(output_file_path), "w", encoding="utf-8") as f:
        for i, (start, end, text) in enumerate(all_entries, start=1):
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")


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
