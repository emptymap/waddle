import os
from pathlib import Path


def time_to_seconds(timestamp: str) -> float:
    """
    Convert SRT timestamp format (hh:mm:ss,ms) to seconds.

    Args:
        timestamp (str): Timestamp in the format "hh:mm:ss,ms".

    Returns:
        float: Time in seconds.
    """
    try:
        hours, minutes, seconds = timestamp.replace(",", ".").split(":")
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except Exception as e:
        raise ValueError(f"Invalid timestamp format: {timestamp}") from e


def phrase_time_to_seconds(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        pass

    value = s.replace(",", ".")
    parts = list(map(float, value.split(":")))

    if len(parts) > 3:
        raise ValueError(f"Invalid time format: {s}")
    weights = [3600, 60, 1][-len(parts) :]

    return float(sum(p * w for p, w in zip(parts, weights, strict=False)))


def format_time(seconds: float) -> str:
    """
    Format seconds to SRT timestamp format (hh:mm:ss,ms).

    Args:
        seconds (float): Time in seconds.

    Returns:
        str: Timestamp in SRT format "hh:mm:ss,ms".
    """
    hh = int(seconds // 3600)
    mm = int((seconds % 3600) // 60)
    ss = int(seconds % 60)
    ms = round((seconds % 1) * 1000)
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"


def format_audio_filename(prefix: str, start: int, end: int) -> str:
    """Generate a standardized audio filename with a given prefix and time range."""
    return f"{prefix}_{start}_{end}.wav"


def parse_audio_filename(filename: str) -> tuple:
    """Extract and return the start and end timestamps from a standardized audio filename."""
    parts = filename.split("_")
    start_str, end_str = parts[-2], parts[-1].split(".")[0]
    return int(start_str), int(end_str)


def to_path(obj: str | bytes | os.PathLike) -> Path:
    """Converts input to a pathlib.Path object, handling str, bytes, and os.PathLike."""
    if isinstance(obj, Path):
        return obj

    fs_path = os.fspath(obj)
    if isinstance(fs_path, (bytes, bytearray, memoryview)):
        fs_path = bytes(fs_path).decode()
    return Path(fs_path)
