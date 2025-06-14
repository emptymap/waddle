import numpy as np
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize


def enhance_audio_quality(audio: AudioSegment, target_dBFS: float = -16.0) -> AudioSegment:
    """Apply audio enhancement processing chain."""
    normalized_audio = normalize(audio)
    compressed_audio = compress_dynamic_range(
        normalized_audio, threshold=-20.0, ratio=4.0, attack=5.0, release=50.0
    )
    limited_audio = apply_limiter(compressed_audio)
    target_audio = match_target_amplitude(limited_audio, target_dBFS)

    return target_audio


def apply_limiter(audio_segment: AudioSegment, threshold: float = -3.0) -> AudioSegment:
    """Apply soft limiting to prevent clipping."""
    samples = np.array(audio_segment.get_array_of_samples())
    max_val = 10 ** (threshold / 20.0) * audio_segment.max_possible_amplitude
    samples = np.tanh(samples / max_val) * max_val
    return audio_segment._spawn(samples.astype(np.int16).tobytes())


def match_target_amplitude(sound: AudioSegment, target_dBFS: float = -16.0) -> AudioSegment:
    """Match loudness to broadcast standards (-16 LUFS for podcasts)."""
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)
