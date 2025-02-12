import os
import tempfile

from waddle.processing.combine import (
    combine_srt_files,
    parse_srt,
)


def create_srt_files_and_parse(temp_dir, srt_files):
    entries_dict = {}
    for filename, content in srt_files.items():
        filename_base = filename.split(".")[0]
        with open(os.path.join(temp_dir, filename), "w", encoding="utf-8") as f:
            f.write(content)
        entries_dict[filename_base] = parse_srt(os.path.join(temp_dir, filename), filename_base)
    return entries_dict


def create_combined_srt_file(temp_dir, srt_files):
    create_srt_files_and_parse(temp_dir, srt_files)
    output_srt = os.path.join(temp_dir, "combined.srt")
    combine_srt_files(temp_dir, output_srt)
    assert os.path.exists(os.path.join(temp_dir, "combined.srt")), "Combined SRT file not found."
    return parse_srt(output_srt)


def check_srt_entry(entry: tuple, expected_start: str, expected_end: str, expected_text: str):
    assert entry[0] == expected_start, f"Start time mismatch: {entry[0]} != {expected_start}"
    assert entry[1] == expected_end, f"End time mismatch: {entry[1]} != {expected_end}"
    assert entry[2] == expected_text, f"Text mismatch: {entry[2]} != {expected_text}"


def test_parse_srt_empty_file():
    """Test parsing an empty SRT file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        entries_dict = create_srt_files_and_parse(temp_dir, {"empty.srt": ""})
        assert entries_dict["empty"] == [], "Parsing an empty file should return an empty list."


def test_parse_srt_single_entry():
    """Test parsing an SRT file with a single entry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "single.srt": ("1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"),
        }
        entries_dict = create_srt_files_and_parse(temp_dir, srt_files)
        len(entries_dict["single"]) == 1, "Single entry should be parsed."
        check_srt_entry(
            entries_dict["single"][0], "00:00:00.000", "00:00:05.000", "single: Hello world."
        )


def test_parse_srt_multiple_entries():
    """Test parsing an SRT file with multiple entries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "multiple.srt": (
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:05,000 --> 00:00:10,000\nHow are you?\n\n"
                "3\n00:00:10,000 --> 00:00:15,000\nI'm fine, thanks.\n\n"
            ),
        }
        entries_dict = create_srt_files_and_parse(temp_dir, srt_files)
        assert len(entries_dict["multiple"]) == 3, "Three entries should be parsed."
        check_srt_entry(
            entries_dict["multiple"][0], "00:00:00.000", "00:00:05.000", "multiple: Hello world."
        )
        check_srt_entry(
            entries_dict["multiple"][1], "00:00:05.000", "00:00:10.000", "multiple: How are you?"
        )
        check_srt_entry(
            entries_dict["multiple"][2],
            "00:00:10.000",
            "00:00:15.000",
            "multiple: I'm fine, thanks.",
        )


def test_parse_srt_multiple_entries_with_broken():
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "multiple.srt": (
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:05,000 --> 00:00:10,000\nHow are you?\n"  # Not 2 newlines
                "3\n00:00:15,000 --> 00:00:20,000\nI'm fine, thanks.\n\n"
                "4\n00:00:25,000 --> 00:00:30,000 What's up?\n\n"  # Missing newline after timestamp
                "5\n00:00:35,000 --> 00:00:40,000\nI'm good.\n\n"
            ),
        }
        entries_dict = create_srt_files_and_parse(temp_dir, srt_files)
        assert len(entries_dict["multiple"]) == 3, "2 and 3 should be together, and 4 is skipped."
        check_srt_entry(
            entries_dict["multiple"][0],
            "00:00:00.000",
            "00:00:05.000",
            "multiple: Hello world.",
        )
        check_srt_entry(
            entries_dict["multiple"][2],
            "00:00:35.000",
            "00:00:40.000",
            "multiple: I'm good.",
        )


def test_combine_srt_files_empty_directory():
    """Test combining SRT files when the input directory is empty."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_srt = os.path.join(temp_dir, "combined.srt")

        combine_srt_files(temp_dir, output_srt)

        assert os.path.exists(output_srt), "Combined SRT file was not created."
        with open(output_srt, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == "", "Combined SRT file should be empty when no input SRT files exist."


def test_combine_srt_files_single_file():
    """Test combining a single SRT file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "speaker1.srt": "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n",
        }
        entries = create_combined_srt_file(temp_dir, srt_files)

        check_srt_entry(entries[0], "00:00:00.000", "00:00:05.000", "speaker1: Hello world.")


def test_combine_srt_files_multiple_files():
    """Test combining multiple SRT files and sorting by timestamps."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "speaker1.srt": "1\n00:00:05,000 --> 00:00:10,000\nHow are you?\n\n",
            "ep0-speaker2.srt": (  # hyphenated name
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:15,000 --> 00:00:20,000\nWhat's up?\n\n"
            ),
            "speaker3.srt": (
                "1\n00:00:10,000 --> 00:00:15,000\nI'm fine, thanks.\n\n"
                "2\n00:00:20,000 --> 00:00:25,000\nI'm good.\n\n"
            ),
        }
        entries = create_combined_srt_file(temp_dir, srt_files)

        assert len(entries) == 5, "Unexpected number of entries in combined SRT file."
        check_srt_entry(entries[0], "00:00:00.000", "00:00:05.000", "speaker2: Hello world.")
        check_srt_entry(entries[1], "00:00:05.000", "00:00:10.000", "speaker1: How are you?")
        check_srt_entry(entries[2], "00:00:10.000", "00:00:15.000", "speaker3: I'm fine, thanks.")
        check_srt_entry(entries[3], "00:00:15.000", "00:00:20.000", "speaker2: What's up?")
        check_srt_entry(entries[4], "00:00:20.000", "00:00:25.000", "speaker3: I'm good.")


def test_combine_srt_files_with_broken_and_empty_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_files = {
            "ep0-speaker1.srt": "1\n00:00:05,000 --> 00:00:10,000\nI'm fine, thanks.\n\n",
            "broken.srt": (
                "1\n00:00:07,000 --> 00:00:08,000\nI'm good too.\n\n"
                "2\n00:00:01,000 --> 00:00:30,000 Missing newline\n\n"  # Missing newline after text
                "3\n00:00:10,001 --> 00:00:40,000\nThis is next of missing newline.\n\n"
            ),
            "empty.srt": "",
            "speaker2.srt": "1\n00:00:00,000 --> 00:00:06,000\nHow are you?\n\n",
        }
        entries = create_combined_srt_file(temp_dir, srt_files)

        assert len(entries) == 4, "broken.srt should be skipped, and empty.srt should be ignored."
        check_srt_entry(entries[0], "00:00:00.000", "00:00:06.000", "speaker2: How are you?")
        check_srt_entry(entries[1], "00:00:05.000", "00:00:10.000", "speaker1: I'm fine, thanks.")
        check_srt_entry(entries[2], "00:00:07.000", "00:00:08.000", "broken: I'm good too.")
        check_srt_entry(
            entries[3],
            "00:00:10.001",
            "00:00:40.000",
            "broken: This is next of missing newline.",
        )
