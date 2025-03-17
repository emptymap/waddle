import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mutagen.id3 import ID3

# FIXME: Importing from private(?) modules. This is not good but these items are
# not listed in `__all__` so can't be imported directly from the package as in the document.
# ref: https://mutagen.readthedocs.io/en/latest/user/id3.html#chapter-extension
from mutagen.id3._frames import CHAP, CTOC, TIT2
from mutagen.id3._specs import CTOCFlags

from waddle.audios.call_tools import convert_to_mp3


def generate_metadata(
    source_file: os.PathLike[Any] | str,
    audio_file: os.PathLike[Any] | str | None,
    output_dir: os.PathLike[Any] | str,
):
    source_file_path = Path(source_file)
    if not source_file_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_file}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source = source_file_path.read_text(encoding="utf-8")
    entries = parse_annotated_srt(source)
    chapters, show_notes = extract_metadata(entries)

    base_name = source_file_path.stem
    chapter_file_path = Path(output_dir) / f"{base_name}.chapters.txt"
    show_notes_file_path = Path(output_dir) / f"{base_name}.show_notes.md"

    chapter_file_path.write_text(format_chapters(chapters), encoding="utf-8")
    show_notes_file_path.write_text(show_notes, encoding="utf-8")

    if audio_file is None:
        # check if the audio file with the same stem exists
        for ext in ["mp3", "m4a", "wav"]:
            audio_file_path = source_file_path.with_suffix(f".{ext}")
            if audio_file_path.is_file():
                print(f"[INFO] Found audio file: {audio_file_path}")
                audio_file = audio_file_path
                break
        else:
            print(f"[INFO] Audio file not found for: {source_file}")
            return

    audio_file_path = Path(audio_file)
    if not audio_file_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_file}")

    output_audio_path = output_dir / f"{audio_file_path.stem}.mp3"
    if audio_file_path.suffix == ".mp3":
        shutil.copy(audio_file_path, output_audio_path)
    else:
        convert_to_mp3(audio_file_path, output_audio_path)

    embed_chapter_info(output_audio_path, chapters)


@dataclass
class Chapter:
    start: float
    """Start time in seconds"""
    end: float
    """End time in seconds"""
    title: str
    """Chapter title"""
    level: int
    """Chapter level"""


@dataclass
class ChapterMarker:
    title: str
    level: int
    raw: str


@dataclass
class ShowNotesEntry:
    text: str


@dataclass
class SRTEntry:
    index: int
    """Subtitle index"""
    start: float
    """Start time in seconds"""
    end: float
    """End time in seconds"""
    speaker: str
    """Speaker name"""
    text: str
    """Subtitle text"""
    raw: str
    """Raw subtitle entry"""


def extract_metadata(
    entries: list[ChapterMarker | ShowNotesEntry | SRTEntry],
) -> tuple[list[Chapter], str]:
    chapters: list[Chapter] = []
    show_notes = ""

    # last SRT entry in this file
    chapter_start_srt_entry = None
    chapter_end_srt_entry = None
    for entry in reversed(entries):
        if isinstance(entry, SRTEntry):
            if chapter_end_srt_entry is None:
                chapter_end_srt_entry = entry
            chapter_start_srt_entry = entry
        if isinstance(entry, ChapterMarker):
            if chapter_start_srt_entry and chapter_end_srt_entry:
                chapters.insert(
                    0,
                    Chapter(
                        start=chapter_start_srt_entry.start,
                        end=chapter_end_srt_entry.end,
                        title=entry.title,
                        level=entry.level,
                    ),
                )
            chapter_start_srt_entry = None
            chapter_end_srt_entry = None
        if isinstance(entry, ShowNotesEntry):
            show_notes = entry.text + "\n" + show_notes

    return chapters, show_notes


def parse_annotated_srt(annotated_srt: str) -> list[ChapterMarker | ShowNotesEntry | SRTEntry]:
    s = annotated_srt
    items: list[ChapterMarker | ShowNotesEntry | SRTEntry] = []

    while s != "":
        # try to match an SRT entry
        srt_entry = match_srt_entry(s)
        if srt_entry:
            items.append(srt_entry)
            s = s[len(srt_entry.raw) :]
            continue
        # then try to match a chapter marker
        chapter_marker = match_chapter_marker(s)
        if chapter_marker:
            items.append(chapter_marker)
            s = s[len(chapter_marker.raw) :]
            continue
        # treat just the first line as show notes
        first_newline = s.find("\n")
        if first_newline != -1:
            show_notes_line = s[:first_newline]
            if show_notes_line.strip("\n ") != "":
                if show_notes_line.startswith(";"):
                    show_notes_line = show_notes_line[1:].strip()
                items.append(ShowNotesEntry(text=show_notes_line))
            s = s[first_newline + 1 :]
        else:
            # If there's no newline, treat all remaining text as show notes
            items.append(ShowNotesEntry(text=s))
            s = ""
    return items


srt_pattern = re.compile(
    r"^(\d+)\n(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n([^:]+): (.+)(?:\n\n|$)"
)


def match_srt_entry(s: str) -> SRTEntry | None:
    m = srt_pattern.match(s)
    if not m:
        return None
    return SRTEntry(
        index=int(m.group(1)),
        start=parse_time(m.group(2)),
        end=parse_time(m.group(3)),
        speaker=m.group(4),
        text=m.group(5),
        raw=m.group(0),
    )


def parse_time(ts: str) -> float:
    """Convert timestamp string to seconds."""
    h, m, s = map(float, ts.split(":"))
    return h * 3600 + m * 60 + s


chapter_pattern = re.compile(r"^(#{1,6}) (.+)\n")


def match_chapter_marker(s: str) -> ChapterMarker | None:
    m = chapter_pattern.match(s)
    if not m:
        return None
    level = len(m.group(1))
    title = m.group(2).strip()
    return ChapterMarker(title=title, level=level, raw=m.group(0))


def format_time(seconds: float) -> str:
    if seconds >= 3600:
        return f"{int(seconds // 3600):02d}:{int(seconds // 60 % 60):02d}:{int(seconds % 60):02d}"
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def format_chapters(chapters: list[Chapter]) -> str:
    return "\n".join(f"- ({format_time(chapter.start)}) {chapter.title}" for chapter in chapters)


def embed_chapter_info(mp3_file: Path, chapters: list[Chapter]):
    print(f"[INFO] Embedding chapter information in: {mp3_file}")
    audio = ID3(str(mp3_file))

    # Remove existing chapter information
    audio.delall("CTOC")
    audio.delall("CHAP")

    audio.add(
        CTOC(
            element_id="toc",
            flags=CTOCFlags.TOP_LEVEL | CTOCFlags.ORDERED,
            child_ids=[f"ch{idx + 1}".encode("utf-8") for idx, _ in enumerate(chapters)],
        )
    )

    for idx, chapter in enumerate(chapters):
        audio.add(
            CHAP(
                element_id=f"ch{idx + 1}".encode("utf-8"),
                start_time=int(chapter.start * 1000),
                end_time=int(chapter.end * 1000),
                sub_frames=[
                    TIT2(text=chapter.title),
                ],
            )
        )
    audio.save()
