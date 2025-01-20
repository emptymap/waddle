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
    ms = int((seconds % 1) * 1000)
    return f"{hh:02}:{mm:02}:{ss:02},{ms:03}"
