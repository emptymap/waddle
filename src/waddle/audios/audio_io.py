from pathlib import Path

import numpy as np


def read_wave(
    file_path: Path, duration: int | None = None, mono: bool = True, sr: int | None = None
) -> tuple[np.ndarray, int]:
    """Reads a WAV file and returns the audio data and sample rate."""
    # Dummy
    audio = np.zeros(100)
    sample_rate = 48000
    return audio, sample_rate


def write_wave(file_path: Path, audio: np.ndarray, sample_rate: int) -> None:
    """Writes audio data to a WAV file."""
    pass
