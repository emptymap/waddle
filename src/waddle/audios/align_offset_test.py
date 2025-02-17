import tempfile
import wave
from pathlib import Path

import numpy as np

from waddle.audios.align_offset import (
    align_speaker_to_reference,
    find_offset_via_cross_correlation,
    shift_audio,
)

DEFAULT_SR = 48000


def generate_test_audio(sr=DEFAULT_SR, s_padding=0, e_padding=0):
    """
    Generate a test audio with s_padding seconds of silence, followed by 1 second of sine wave,
    followed by e_padding seconds of silence.
    """
    t = np.linspace(0, np.pi / 2, int(sr * 1.0), endpoint=False)
    sine_wave = (32767 * 0.5 * np.sin(t)).astype(np.float32)

    s_silence = np.zeros(sr + s_padding, dtype=np.float32)  # 1s + s_padding
    e_silence = np.zeros(sr + e_padding, dtype=np.float32)  # 1s + e_padding
    audio = np.concatenate([s_silence, sine_wave, e_silence])

    return audio, sr


def write_wav(file_path, audio, sr):
    """Write an audio file in WAV format."""
    with wave.open(str(file_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sr)
        wav_file.writeframes(audio.tobytes())


def read_wav(file_path):
    """Read an audio file in WAV format."""
    with wave.open(str(file_path), "r") as wav_file:
        sr = wav_file.getframerate()
        audio = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.float32)
    return audio, sr


def test_find_offset_via_cross_correlation():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_padding=24000)

    offset = find_offset_via_cross_correlation(ref_audio, spk_audio)
    assert offset == -24000  # offset should be negative to align the speaker to the reference


def test_shift_audio_s_padding():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_padding=4800)
    shifted = shift_audio(spk_audio, -4800, len(ref_audio))
    assert np.allclose(ref_audio, shifted)


def test_shift_audio_e_padding():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(e_padding=158)
    shifted = shift_audio(spk_audio, 0, len(ref_audio))
    assert len(shifted) == len(ref_audio)
    assert np.allclose(ref_audio, shifted)


def test_shift_audio_both():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_padding=800, e_padding=555)
    shifted = shift_audio(spk_audio, -800, len(ref_audio))
    assert len(shifted) == len(ref_audio)
    assert np.allclose(ref_audio, shifted)


def test_align_speaker_to_reference():
    with tempfile.TemporaryDirectory() as temp_dir:
        ref_audio, sr = generate_test_audio()
        spk_audio_0, _ = generate_test_audio(s_padding=4800, e_padding=100)
        spk_audio_1, _ = generate_test_audio(e_padding=800)

        temp_dir_path = Path(temp_dir)
        ref_path = temp_dir_path / "ref.wav"
        spk_path_0 = temp_dir_path / "spk_0.wav"
        spk_path_1 = temp_dir_path / "spk_1.wav"

        write_wav(ref_path, ref_audio, sr)
        write_wav(spk_path_0, spk_audio_0, sr)
        write_wav(spk_path_1, spk_audio_1, sr)

        output_path_0 = align_speaker_to_reference(ref_path, spk_path_0, temp_dir_path)
        output_path_1 = align_speaker_to_reference(ref_path, spk_path_1, temp_dir_path)

        aligned_audio_0, _ = read_wav(output_path_0)
        aligned_audio_1, _ = read_wav(output_path_1)

        assert len(aligned_audio_0) == len(ref_audio)
        assert len(aligned_audio_1) == len(ref_audio)

        assert np.allclose(ref_audio, aligned_audio_0)
        assert np.allclose(ref_audio, aligned_audio_1)
