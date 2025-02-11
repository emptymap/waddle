def time_to_seconds(timestamp: str) -> float:
    """
    Convert SRT timestamp format (hh:mm:ss,ms) to seconds.

    Args:
        timestamp (str): Timestamp in the format "hh:mm:ss,ms".

    Returns:
        float: Time in seconds.
    """
    hours, minutes, seconds = timestamp.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


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
    start_str, end_str = parts[1], parts[2].split(".")[0]
    return int(start_str), int(end_str)
