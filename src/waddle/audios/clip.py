import wave
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WaveParams:
    """Parameters for a WAV file."""

    frame_rate: int
    n_channels: int
    samp_width: int
    n_frames: int


def read_wave_params(wav_file: wave.Wave_read) -> WaveParams:
    """Read parameters from a WAV file."""
    return WaveParams(
        frame_rate=wav_file.getframerate(),
        n_channels=wav_file.getnchannels(),
        samp_width=wav_file.getsampwidth(),
        n_frames=wav_file.getnframes(),
    )


def calculate_frame_range(
    params: WaveParams, start_time: float, duration: float | None = None
) -> tuple[int, int]:
    """Calculate start and end frame positions."""
    start_frame = int(start_time * params.frame_rate)
    if duration is None:
        end_frame = params.n_frames
    else:
        end_frame = start_frame + int(duration * params.frame_rate)

    # Ensure frames are within valid range
    start_frame = max(0, min(start_frame, params.n_frames))
    end_frame = max(start_frame, min(end_frame, params.n_frames))

    return start_frame, end_frame


def read_frames(wav_file: wave.Wave_read, start_frame: int, end_frame: int) -> bytes:
    """Read frames from WAV file."""
    wav_file.setpos(start_frame)
    return wav_file.readframes(end_frame - start_frame)


def write_wave_file(out_path: Path, params: WaveParams, frames: bytes) -> None:
    """Write frames to a new WAV file."""
    with wave.open(str(out_path), "wb") as output_wav:
        output_wav.setnchannels(params.n_channels)
        output_wav.setsampwidth(params.samp_width)
        output_wav.setframerate(params.frame_rate)
        output_wav.writeframes(frames)


def clip_audio(
    audio_path: Path, out_path: Path, ss: float = 0.0, out_duration: float | None = None
) -> Path:
    """
    Clip an audio file to a specified duration starting from a given time.

    Args:
        audio_path: Path to the input audio file
        out_path: Path to save the output audio file
        ss: Start time in seconds (default: 0.0)
        out_duration: Duration in seconds for the output audio (default: None)

    Returns:
        Path to the clipped audio file

    Raises:
        wave.Error: If there are issues reading/writing the WAV file
        ValueError: If the start time or duration are invalid
    """
    try:
        with wave.open(str(audio_path), "rb") as wav:
            # Get wave parameters
            params = read_wave_params(wav)

            # Calculate frame range
            start_frame, end_frame = calculate_frame_range(params, ss, out_duration)

            # Read frames
            frames = read_frames(wav, start_frame, end_frame)

        # Write output file
        write_wave_file(out_path, params, frames)

        return audio_path

    except wave.Error as e:
        raise wave.Error(f"Error processing WAV file: {e}")
    except Exception as e:
        raise ValueError(f"Error clipping audio: {e}")
