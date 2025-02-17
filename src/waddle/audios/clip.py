import wave
from pathlib import Path


def clip_audio(
    audio_path: Path, out_path: Path, ss: float = 0.0, out_duration: float | None = None
) -> Path:
    """
    Clip an audio file to a specified duration starting from a given time.

    Args:
        audio_path (str): Path to the input audio file.
        ss (float): Start time in seconds (default: 0.0).
        out_duration (float | None): Duration in seconds for the output audio (default: None).

    Returns:
        str: Path to the clipped audio file.
    """
    with wave.open(str(audio_path), "rb") as wav:
        frame_rate = wav.getframerate()
        n_channels = wav.getnchannels()
        samp_width = wav.getsampwidth()

        start_frame = int(ss * frame_rate)
        if out_duration is None:
            end_frame = wav.getnframes()
        else:
            end_frame = start_frame + int(out_duration * frame_rate)

        wav.setpos(start_frame)
        frames = wav.readframes(end_frame - start_frame)

    with wave.open(str(out_path), "wb") as output_wav:
        output_wav.setnchannels(n_channels)
        output_wav.setsampwidth(samp_width)
        output_wav.setframerate(frame_rate)
        output_wav.writeframes(frames)

    return audio_path
