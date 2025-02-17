import os
from pathlib import Path

import pytest

from waddle.utils import (
    format_audio_filename,
    format_time,
    parse_audio_filename,
    phrase_time_to_seconds,
    time_to_seconds,
    to_path,
)


def test_time_to_seconds():
    """Test conversion of SRT timestamps to seconds."""
    assert time_to_seconds("00:00:00,000") == 0.0, "time_to_seconds('00:00:00,000') is failed."
    assert time_to_seconds("00:01:30,500") == 90.5, "time_to_seconds('00:01:30,500') is failed."
    assert time_to_seconds("01:23:45,678") == 5025.678, "time_to_seconds('01:23:45,678') is failed."
    assert time_to_seconds("12:34:56,789") == 45296.789, (
        "time_to_seconds('12:34:56,789') is failed."
    )
    assert time_to_seconds("99:59:59,999") == 359999.999, (
        "time_to_seconds('99:59:59,999') is failed."
    )

    with pytest.raises(ValueError):
        time_to_seconds("00:00:00:00")
    with pytest.raises(ValueError):
        time_to_seconds("00:00:00.123.53")
    with pytest.raises(ValueError):
        time_to_seconds("00:00.123")
    with pytest.raises(ValueError):
        time_to_seconds("00.12")


def test_phrase_time_to_seconds():
    """Test conversion of argument timestamps to seconds."""
    assert phrase_time_to_seconds("00:01") == 1.0
    assert phrase_time_to_seconds("00:01.5") == 1.5
    assert phrase_time_to_seconds("05:12") == 312.0
    assert phrase_time_to_seconds("05:12.5") == 312.5
    assert phrase_time_to_seconds("12") == 12.0
    assert phrase_time_to_seconds("12.5") == 12.5
    assert phrase_time_to_seconds("12:34:56") == 45296.0
    assert phrase_time_to_seconds("12:34:56.789") == 45296.789
    assert phrase_time_to_seconds("00:1.5:00") == 90.0
    assert phrase_time_to_seconds("00:1.5:10") == 100.0
    assert phrase_time_to_seconds("0.1:0.2:0.3") == 372.3


def test_format_time():
    """Test formatting of seconds into SRT timestamp format."""
    assert format_time(0.0) == "00:00:00,000", "format_time(0.0) is failed."
    assert format_time(90.5) == "00:01:30,500", "format_time(90.5) is failed."
    assert format_time(5025.678) == "01:23:45,678", "format_time(5025.678) is failed."
    assert format_time(45296.789) == "12:34:56,789", "format_time(45296.789) is failed."
    assert format_time(359999.999) == "99:59:59,999", "format_time(359999.999) is failed."


def test_format_audio_filename():
    """Test get segs/chunks name."""
    assert format_audio_filename("chunk", 0, 100) == "chunk_0_100.wav", (
        "get_name('chunk', 0, 100) is failed."
    )
    assert format_audio_filename("chunk", 1, 200) == "chunk_1_200.wav", (
        "get_name('chunk', 1, 200) is failed."
    )
    assert format_audio_filename("seg", 1, 10) == "seg_1_10.wav", (
        "get_name('seg', 1, 10) is failed."
    )
    assert format_audio_filename("seg", 10, 20) == "seg_10_20.wav", (
        "get_name('seg', 10, 20) is failed."
    )


def test_parse_audio_filename():
    """Test parse segs/chunks to get start and end."""
    assert parse_audio_filename("chunk_0_100.wav") == (0, 100), (
        "parse_name('chunk_0_100.wav') is failed."
    )
    assert parse_audio_filename("chunk_1_200.wav") == (1, 200), (
        "parse_name('chunk_1_200.wav') is failed."
    )
    assert parse_audio_filename("seg_1_10.wav") == (1, 10), "parse_name('seg_1_10.wav') is failed."
    assert parse_audio_filename("seg_10_20.wav") == (10, 20), (
        "parse_name('seg_10_20.wav') is failed."
    )

    # Other folder
    assert parse_audio_filename("folder/chunk_0_100.wav") == (0, 100), (
        "parse_name('folder/chunk_0_100.wav') is failed."
    )
    assert parse_audio_filename("../folder/seg_1_200.wav") == (1, 200), (
        "parse_name('../folder/seg_1_200.wav') is failed."
    )

    # _ is used in the folder name
    assert parse_audio_filename("tmp/kzjirwe_klae256_wj1/seg_1_200.wav") == (1, 200), (
        "parse_name('tmp/kzjirwe_klae256_wj1/seg_1_200.wav') is failed."
    )


class PathLikeBytes(os.PathLike):
    """Custom os.PathLike class returning bytes."""

    def __init__(self, path: bytes):
        if not isinstance(path, bytes):
            raise TypeError("Path must be a bytes object")
        self._path = path

    def __fspath__(self) -> bytes:
        return self._path


def test_to_path():
    """Test convert string to Path."""
    assert to_path(Path("abc/23/a.txt")) == Path("abc/23/a.txt")
    assert to_path("test") == Path("test")
    assert to_path("test/test") == Path("test/test")
    assert to_path(os.path.join("test", "test")) == Path("test/test")
    assert to_path(b"z/1/2") == Path("z/1/2")
    assert to_path(b"test/test.png") == Path("test/test.png")
    assert to_path(PathLikeBytes(b"a/b.py")) == Path("a/b.py")
