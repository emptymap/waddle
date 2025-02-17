from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy import signal

from waddle.config import (
    DEFAULT_COMP_AUDIO_DURATION,
    DEFAULT_SR,
)


def find_offset_via_cross_correlation(ref_audio: np.ndarray, spk_audio: np.ndarray) -> int:
    """
    Return the sample offset (lag) that best aligns spk_audio to ref_audio
    using cross-correlation.

    Positive offset => spk_audio starts earlier than ref_audio
    Negative offset => spk_audio starts later than ref_audio
    """
    correlation = signal.correlate(ref_audio, spk_audio, mode="full")
    max_corr_index = int(np.argmax(correlation))
    offset = max_corr_index - (
        len(spk_audio) - 1
    )  # the center index (zero lag) is at len(spk_audio) - 1
    return offset


def shift_audio(spk_audio: np.ndarray, offset: int, ref_length: int) -> np.ndarray:
    """
    Shift the spk_audio by 'offset' samples relative to the reference track.
    Ensures the returned array is the same length as the reference.
    """
    if offset > 0:
        shifted = np.pad(spk_audio, (offset, 0), mode="constant", constant_values=0)
    elif offset < 0:
        skip = abs(offset)
        if skip >= len(spk_audio):
            shifted = np.zeros(ref_length, dtype=spk_audio.dtype)
        else:
            shifted = spk_audio[skip:]
    else:
        shifted = spk_audio

    if len(shifted) > ref_length:
        shifted = shifted[:ref_length]
    elif len(shifted) < ref_length:
        shifted = np.pad(
            shifted, (0, ref_length - len(shifted)), mode="constant", constant_values=0
        )

    return shifted


def align_speaker_to_reference(
    reference_path: Path,
    speaker_path: Path,
    output_dir: Path = Path("out"),
    sample_rate: int = DEFAULT_SR,
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
) -> Path:
    # 1) Load short segments for cross-correlation
    ref_audio, _ = librosa.load(
        str(reference_path), sr=sample_rate, mono=True, duration=comp_duration
    )
    spk_audio, _ = librosa.load(
        str(speaker_path), sr=sample_rate, mono=True, duration=comp_duration
    )

    # Normalize
    if np.max(np.abs(ref_audio)) > 0:
        ref_audio /= np.max(np.abs(ref_audio))
    if np.max(np.abs(spk_audio)) > 0:
        spk_audio /= np.max(np.abs(spk_audio))

    # 2) Compute offset
    offset = find_offset_via_cross_correlation(ref_audio, spk_audio)

    # 3) Load full audio
    ref_full, _ = librosa.load(str(reference_path), sr=sample_rate, mono=True)
    spk_full, _ = librosa.load(str(speaker_path), sr=sample_rate, mono=True)

    # 4) Shift speaker
    aligned_speaker = shift_audio(spk_full, offset, len(ref_full))

    # 5) Save the aligned track
    output_dir.mkdir(parents=True, exist_ok=True)
    speaker_base = speaker_path.name
    aligned_path = output_dir / speaker_base
    sf.write(aligned_path, aligned_speaker, sample_rate)
    return aligned_path
