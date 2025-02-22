import os
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

# Type aliases for clarity
TimeComponents: TypeAlias = tuple[int, int, float]  # hours, minutes, seconds
AudioTimeRange: TypeAlias = tuple[int, int]  # start_ms, end_ms


@dataclass
class TimeFormat:
    """Time format configuration."""

    separator: str = ":"
    decimal: str = "."
    ms_separator: str = ","


def parse_time_components(timestamp: str, format: TimeFormat = TimeFormat()) -> TimeComponents:
    """Parse timestamp string into hours, minutes, and seconds components."""
    try:
        # Handle decimal seconds format
        if format.decimal in timestamp:
            seconds = float(timestamp)
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return hours, minutes, remaining_seconds

        # Replace milliseconds separator with decimal point for proper float parsing
        parts = timestamp.replace(format.ms_separator, format.decimal).split(format.separator)

        if len(parts) > 3:
            raise ValueError(f"Too many time components in: {timestamp}")

        # Convert parts to appropriate numeric types
        components = [float(p) if i == len(parts) - 1 else int(p) for i, p in enumerate(parts)]

        # Pad with zeros if needed
        while len(components) < 3:
            components.insert(0, 0)

        return tuple(components)  # type: ignore

    except Exception as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e


def components_to_seconds(components: TimeComponents) -> float:
    """Convert time components to total seconds."""
    hours, minutes, seconds = components
    return hours * 3600 + minutes * 60 + seconds


def time_to_seconds(timestamp: str) -> float:
    """
    Convert SRT timestamp format (hh:mm:ss,ms) to seconds.

    Args:
        timestamp: Timestamp in the format "hh:mm:ss,ms"

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If timestamp format is invalid
    """
    components = parse_time_components(timestamp)
    return components_to_seconds(components)


def phrase_time_to_seconds(timestamp: str) -> float:
    """
    Convert various time formats to seconds.
    Supports:
    - Decimal seconds ("123.45")
    - MM:SS ("1:23.45")
    - HH:MM:SS ("1:02:03.45")

    Args:
        timestamp: Time string in supported format

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If time format is invalid
    """
    components = parse_time_components(timestamp, TimeFormat(decimal="."))
    return components_to_seconds(components)


def format_time(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (hh:mm:ss,ms).

    Args:
        seconds: Time in seconds

    Returns:
        Timestamp in SRT format "hh:mm:ss,ms"

    Raises:
        ValueError: If seconds value is negative
    """
    if seconds < 0:
        raise ValueError("Time value cannot be negative")

    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    ms = round((seconds % 1) * 1000)

    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def format_audio_filename(prefix: str, start: int, end: int) -> str:
    """
    Generate a standardized audio filename with a given prefix and time range.

    Args:
        prefix: Filename prefix
        start: Start time in milliseconds
        end: End time in milliseconds

    Returns:
        Formatted filename string

    Raises:
        ValueError: If start time is greater than end time
    """
    if start > end:
        raise ValueError(f"Start time ({start}) cannot be greater than end time ({end})")
    return f"{prefix}_{start}_{end}.wav"


def parse_audio_filename(filename: str) -> AudioTimeRange:
    """
    Extract and return the start and end timestamps from a standardized audio filename.

    Args:
        filename: Audio filename in format "prefix_start_end.wav"

    Returns:
        Tuple of (start_ms, end_ms)

    Raises:
        ValueError: If filename format is invalid
    """
    try:
        parts = filename.split("_")
        if len(parts) < 3:
            raise ValueError("Invalid filename format")

        start_str, end_str = parts[-2], parts[-1].split(".")[0]
        start, end = int(start_str), int(end_str)

        if start > end:
            raise ValueError(f"Start time ({start}) cannot be greater than end time ({end})")

        return start, end

    except Exception as e:
        raise ValueError(f"Invalid audio filename format: {filename}") from e


def to_path(obj: str | bytes | os.PathLike) -> Path:
    """
    Convert input to a pathlib.Path object.

    Args:
        obj: Input path as string, bytes, or PathLike object

    Returns:
        Path object

    Raises:
        TypeError: If input type is not supported
        ValueError: If path string is invalid
    """
    try:
        if isinstance(obj, Path):
            return obj

        fs_path = os.fspath(obj)
        if isinstance(fs_path, (bytes, bytearray, memoryview)):
            fs_path = bytes(fs_path).decode()
        return Path(fs_path)

    except Exception as e:
        raise ValueError(f"Invalid path: {obj}") from e
