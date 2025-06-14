from pathlib import Path

import noisereduce as nr
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

    # Compress loud peaks
    threshold = 0.6
    compressed = np.where(
        np.abs(boosted) > threshold,
        np.sign(boosted) * (threshold + (np.abs(boosted) - threshold) * 0.15),
        boosted,
    )

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


def nr_reduce_noise(audio: type_path_or_seg, noise_segment=None) -> AudioSegment:
    """
    Apply noise reduction to a pydub AudioSegment using noisereduce.

    Args:
        audio_segment: pydub AudioSegment containing the audio to denoise
        noise_segment: Optional pydub AudioSegment containing noise sample

    Returns:
        pydub AudioSegment with noise reduced
    """
    audio_seg = audio_path_or_seg(audio)
    audio_data = np.array(audio_seg.get_array_of_samples(), dtype=np.float32)

    # Reshape audio data if stereo
    if audio_seg.channels == 2:
        audio_data = audio_data.reshape((-1, 2)).T
    if audio_seg.sample_width == 2:  # 16-bit
        audio_data = audio_data / 32768.0
    elif audio_seg.sample_width == 4:  # 32-bit
        audio_data = audio_data / 2147483648.0

    # Process noise segment if provided
    noise_data = None
    if noise_segment is not None:
        noise_data = np.array(noise_segment.get_array_of_samples(), dtype=np.float32)
        if noise_segment.channels == 2:
            noise_data = noise_data.reshape((-1, 2)).T
        if noise_segment.sample_width == 2:
            noise_data = noise_data / 32768.0
        elif noise_segment.sample_width == 4:
            noise_data = noise_data / 2147483648.0

    # Apply noise reduction
    reduced_noise = nr.reduce_noise(
        y=audio_data,
        sr=audio_seg.frame_rate,
        y_noise=noise_data,
        prop_decrease=0.7,
        stationary=True,
        n_std_thresh_stationary=2.0,
        freq_mask_smooth_hz=250,
        time_mask_smooth_ms=25,
        n_fft=512,
        hop_length=128,
    )

    # Convert back to AudioSegment
    if audio_seg.sample_width == 2:
        reduced_noise = (reduced_noise * 32767).astype(np.int16)
    elif audio_seg.sample_width == 4:
        reduced_noise = (reduced_noise * 2147483647).astype(np.int32)
    if audio_seg.channels == 2:
        reduced_noise = reduced_noise.T.flatten()

    return AudioSegment(
        data=reduced_noise.tobytes(),
        sample_width=audio_seg.sample_width,
        frame_rate=audio_seg.frame_rate,
        channels=audio_seg.channels,
    )
