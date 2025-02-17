import tempfile
from pathlib import Path
from typing import Dict, TypeAlias

from waddle.processing.combine import SrtEntries, SrtEntry, combine_srt_files, parse_srt

SrtFiles: TypeAlias = dict[str, str]


def create_srt_files(temp_dir: Path, srt_files: SrtFiles, is_combined: bool = False) -> None:
    temp_dir = Path(temp_dir)
    for filename, content in srt_files.items():
        (temp_dir / f"{filename}.srt").write_text(content, encoding="utf-8")

    if is_combined:
        output_srt = temp_dir / "combined.srt"
        combine_srt_files(temp_dir, output_srt)
        assert output_srt.exists(), "Combined SRT file was not created."


def check_srt_entries(temp_dir: Path, expected_srt_files: Dict[str, SrtEntries]):
    temp_dir = Path(temp_dir)
    for filename, expected_entries in expected_srt_files.items():
        entries = parse_srt(temp_dir / f"{filename}.srt")
        assert len(entries) == len(expected_entries), "Number of entries mismatch."
        for i, entry in enumerate(entries):
            check_srt_entry(entry, expected_entries[i])


def check_srt_entry(entry: SrtEntry, expected_entry: SrtEntry):
    assert entry[0] == expected_entry[0], f"Start time mismatch: {entry[0]} != {expected_entry[0]}"
    assert entry[1] == expected_entry[1], f"End time mismatch: {entry[1]} != {expected_entry[1]}"
    assert entry[2] == expected_entry[2], f"Text mismatch: {entry[2]} != {expected_entry[2]}"


def test_parse_srt_empty_file():
    """Test parsing an empty SRT file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "empty": "",
        }
        create_srt_files(temp_dir_path, srt_files)

        expected_srt_files = {"empty": []}
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_parse_srt_single_entry():
    """Test parsing an SRT file with a single entry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "single": ("1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"),
        }
        create_srt_files(temp_dir_path, srt_files)

        expected_srt_files = {"single": [("00:00:00.000", "00:00:05.000", "Hello world.")]}
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_parse_srt_multiple_entries():
    """Test parsing an SRT file with multiple entries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "multiple": (
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:05,000 --> 00:00:10,000\nHow are you?\n\n"
                "3\n00:00:10,000 --> 00:00:15,000\nI'm fine, thanks.\n\n"
            ),
        }
        create_srt_files(temp_dir_path, srt_files)

        expected_srt_files = {
            "multiple": [
                ("00:00:00.000", "00:00:05.000", "Hello world."),
                ("00:00:05.000", "00:00:10.000", "How are you?"),
                ("00:00:10.000", "00:00:15.000", "I'm fine, thanks."),
            ]
        }
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_parse_srt_multiple_entries_with_broken():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "multiple": (
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:05,000 --> 00:00:10,000\nHow are you?\n"  # Not 2 newlines
                "3\n00:00:15,000 --> 00:00:20,000\nI'm fine, thanks.\n\n"
                "4\n00:00:25,000 --> 00:00:30,000 What's up?\n\n"  # Missing newline after timestamp
                "5\n00:00:35,000 --> 00:00:40,000\nI'm good.\n\n"
            ),
        }
        create_srt_files(temp_dir_path, srt_files)

        expected_srt_files = {
            "multiple": [
                ("00:00:00.000", "00:00:05.000", "Hello world."),
                (
                    "00:00:05.000",
                    "00:00:10.000",
                    "How are you? 3 00:00:15,000 --> 00:00:20,000 I'm fine, thanks.",
                ),
                ("00:00:35.000", "00:00:40.000", "I'm good."),
            ]
        }
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_combine_srt_files_empty_directory():
    """Test combining SRT files when the input directory is empty."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_srt_path = temp_dir_path / "combined.srt"

        combine_srt_files(temp_dir_path, output_srt_path)

        expected_srt_files = {"combined": []}
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_combine_srt_files_single_file():
    """Test combining a single SRT file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "speaker1": "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n",
        }
        create_srt_files(temp_dir_path, srt_files, is_combined=True)

        expected_srt_files = {
            "combined": [("00:00:00.000", "00:00:05.000", "speaker1: Hello world.")]
        }
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_combine_srt_files_multiple_files():
    """Test combining multiple SRT files and sorting by timestamps."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "speaker1": "1\n00:00:05,000 --> 00:00:10,000\nHow are you?\n\n",
            "ep0-speaker2": (  # hyphenated name
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:15,000 --> 00:00:20,000\nWhat's up?\n\n"
            ),
            "speaker3": (
                "1\n00:00:10,000 --> 00:00:15,000\nI'm fine, thanks.\n\n"
                "2\n00:00:20,000 --> 00:00:25,000\nI'm good.\n\n"
            ),
        }
        create_srt_files(temp_dir_path, srt_files, is_combined=True)

        expected_srt_files = {
            "combined": [
                ("00:00:00.000", "00:00:05.000", "speaker2: Hello world."),
                ("00:00:05.000", "00:00:10.000", "speaker1: How are you?"),
                ("00:00:10.000", "00:00:15.000", "speaker3: I'm fine, thanks."),
                ("00:00:15.000", "00:00:20.000", "speaker2: What's up?"),
                ("00:00:20.000", "00:00:25.000", "speaker3: I'm good."),
            ]
        }
        check_srt_entries(temp_dir_path, expected_srt_files)


def test_combine_srt_files_with_broken_and_empty_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        srt_files = {
            "ep0-speaker1": "1\n00:00:05,000 --> 00:00:10,000\nI'm fine, thanks.\n\n",
            "broken": (
                "1\n00:00:07,000 --> 00:00:08,000\nI'm good too.\n\n"
                "2\n00:00:01,000 --> 00:00:30,000 Missing newline\n\n"  # Missing newline after text
                "3\n00:00:10,001 --> 00:00:40,000\nThis is next of missing newline.\n\n"
            ),
            "empty": "",
            "speaker2": "1\n00:00:00,000 --> 00:00:06,000\nHow are you?\n\n",
        }
        create_srt_files(temp_dir_path, srt_files, is_combined=True)

        expected_srt_files = {
            "combined": [
                ("00:00:00.000", "00:00:06.000", "speaker2: How are you?"),
                ("00:00:05.000", "00:00:10.000", "speaker1: I'm fine, thanks."),
                (
                    "00:00:07.000",
                    "00:00:08.000",
                    "broken: I'm good too.",
                ),
                (
                    "00:00:10.001",
                    "00:00:40.000",
                    "broken: This is next of missing newline.",
                ),
            ]
        }
        check_srt_entries(temp_dir_path, expected_srt_files)
