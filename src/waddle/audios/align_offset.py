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


def load_and_normalize_audio(
    audio_path: Path,
    sample_rate: int,
    duration: float | None = None,
) -> np.ndarray:
    """Load and normalize audio file."""
    audio, _ = librosa.load(str(audio_path), sr=sample_rate, mono=True, duration=duration)

    # Normalize if audio is not silent
    if np.max(np.abs(audio)) > 0:
        audio /= np.max(np.abs(audio))

    return audio


def save_aligned_audio(
    audio: np.ndarray,
    output_dir: Path,
    speaker_path: Path,
    sample_rate: int,
) -> Path:
    """Save aligned audio to file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    aligned_path = output_dir / speaker_path.name
    sf.write(aligned_path, audio, sample_rate)
    return aligned_path


def compute_alignment_offset(
    ref_audio: np.ndarray,
    spk_audio: np.ndarray,
    sample_rate: int,
    comp_duration: float,
) -> int:
    """Compute alignment offset between reference and speaker audio."""
    # Load short segments for cross-correlation
    ref_segment = ref_audio[: int(comp_duration * sample_rate)]
    spk_segment = spk_audio[: int(comp_duration * sample_rate)]

    # Compute offset
    return find_offset_via_cross_correlation(ref_segment, spk_segment)


def align_speaker_to_reference(
    reference_path: Path,
    speaker_path: Path,
    output_dir: Path = Path("out"),
    sample_rate: int = DEFAULT_SR,
    comp_duration: float = DEFAULT_COMP_AUDIO_DURATION,
) -> Path:
    """
    Align speaker audio to reference audio using cross-correlation.

    Args:
        reference_path: Path to reference audio file
        speaker_path: Path to speaker audio file to align
        output_dir: Directory to save aligned audio
        sample_rate: Audio sample rate
        comp_duration: Duration of audio segment to use for comparison

    Returns:
        Path to aligned audio file
    """
    # Load full audio files
    ref_audio = load_and_normalize_audio(reference_path, sample_rate)
    spk_audio = load_and_normalize_audio(speaker_path, sample_rate)

    # Compute alignment offset
    offset = compute_alignment_offset(ref_audio, spk_audio, sample_rate, comp_duration)

    # Align speaker audio
    aligned_speaker = shift_audio(spk_audio, offset, len(ref_audio))

    # Save aligned audio
    return save_aligned_audio(aligned_speaker, output_dir, speaker_path, sample_rate)
