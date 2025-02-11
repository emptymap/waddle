from waddle.utils import format_time, time_to_seconds


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
