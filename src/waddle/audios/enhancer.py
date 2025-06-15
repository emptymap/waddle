from pathlib import Path

import numpy as np
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range

type_path_or_seg = Path | AudioSegment


def audio_path_or_seg(audio: type_path_or_seg) -> AudioSegment:
    """Convert Path to AudioSegment if necessary."""
    return audio if isinstance(audio, AudioSegment) else AudioSegment.from_file(audio)


def simple_loudness_processing(audio: type_path_or_seg) -> AudioSegment:
    """Simple loudness processing: boost overall volume while controlling peaks"""
    audio_seg = audio_path_or_seg(audio)

    # Convert to numpy array for processing
    samples = np.array(audio_seg.get_array_of_samples())
    if audio_seg.channels == 2:
        samples = samples.reshape((-1, 2))

    # Normalize to -1 to 1 range
    samples = samples.astype(np.float32) / (2**15)

    # Boost quiet sounds (makeup gain)
    current_level = np.sqrt(np.mean(samples**2))
    target_level = 0.2
    boost = min(target_level / (current_level + 0.001), 3.0)
    boosted = samples * boost

    # Compress loud peaks using logarithmic compression
    threshold = 0.6
    max_output = 0.9

    # Apply logarithmic scaling to values above threshold
    above_threshold_mask = np.abs(boosted) > threshold
    log_compressed = boosted.copy()

    # For values above threshold, apply logarithmic scaling
    above_threshold_values = np.abs(boosted)[above_threshold_mask]
    log_scaled = threshold + np.log1p(above_threshold_values - threshold)
    log_compressed[above_threshold_mask] = np.sign(boosted[above_threshold_mask]) * log_scaled

    # Scale the entire signal so the maximum value becomes 0.9
    current_max = np.max(np.abs(log_compressed))
    if current_max > 0:
        scale_factor = max_output / current_max
        compressed = log_compressed * scale_factor
    else:
        compressed = log_compressed

    # Prevent clipping
    final = np.clip(compressed, -0.95, 0.95)

    # Convert back to audio
    final_samples = (final * (2**15)).astype(np.int16)
    if audio_seg.channels == 2:
        final_samples = final_samples.flatten()

    return AudioSegment(
        final_samples.tobytes(),
        frame_rate=audio_seg.frame_rate,
        sample_width=audio_seg.sample_width,
        channels=audio_seg.channels,
    )


def enhance_audio_quality(audio: type_path_or_seg) -> AudioSegment:
    """Apply audio enhancement processing chain."""
    audio_seg = audio_path_or_seg(audio)

    audio_seg = normalize_rms(audio_seg)
    audio_seg = compress_dynamic_range(
        audio_seg, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0
    )

    return audio_seg


def normalize_rms(audio: type_path_or_seg, target_rms=-20.0):
    """
    Normalize based on RMS (perceived loudness) rather than peaks
    """
    audio_seg = audio_path_or_seg(audio)
    current_rms = audio_seg.rms
    max_amplitude = audio_seg.max_possible_amplitude * 0.95

    current_dbfs = 20 * np.log10(current_rms / max_amplitude)
    gain_db = target_rms - current_dbfs

    # Apply gain but check for clipping
    normalized = audio_seg + gain_db

    return normalized
