from waddle.utils import format_audio_filename, format_time, parse_audio_filename, time_to_seconds


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
