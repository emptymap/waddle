import numpy as np
from pydub import AudioSegment


def enhance_audio_quality(audio: AudioSegment, target_dBFS: float = -16.0) -> AudioSegment:
    """Apply audio enhancement processing chain."""
    audio = normalize_rms(audio)
    # audio = compress_dynamic_range(audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0)
    audio = apply_limiter(audio)

    return audio


def normalize_rms(audio, target_rms=-20.0):
    """
    Normalize based on RMS (perceived loudness) rather than peaks
    """
    current_rms = audio.rms
    max_amplitude_90 = audio.max_possible_amplitude * 0.90

    current_dbfs = 20 * np.log10(current_rms / max_amplitude_90)
    gain_db = target_rms - current_dbfs

    # Apply gain but check for clipping
    normalized = audio + gain_db

    # # If clipping would occur, reduce gain
    # if normalized.max > max_amplitude_90:
    #     reduction = 20 * np.log10(normalized.max_possible_amplitude / normalized.max)
    #     normalized = audio + (gain_db + reduction - 0.1)  # 0.1 dB headroom

    return normalized


def apply_limiter(audio_segment: AudioSegment, threshold: float = -3.0) -> AudioSegment:
    """Apply soft limiting to prevent clipping."""
    samples = np.array(audio_segment.get_array_of_samples())
    max_val = 10 ** (threshold / 20.0) * audio_segment.max_possible_amplitude
    samples = np.tanh(samples / max_val) * max_val
    return audio_segment._spawn(samples.astype(np.int16).tobytes())
