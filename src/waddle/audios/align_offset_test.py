import os
import tempfile
import wave

import numpy as np

from waddle.audios.align_offset import (
    align_speaker_to_reference,
    find_offset_via_cross_correlation,
    shift_audio,
)

DEFAULT_SR = 48000


def generate_test_audio(sr=DEFAULT_SR, s_offset=0, e_offset=0):
    """Generate a test sine wave audio signal with optional start and end offset."""
    t = np.linspace(0, np.pi / 2, int(sr * 1.0), endpoint=False)
    sine_wave = (32767 * 0.5 * np.sin(t)).astype(np.float32)

    s_silence = np.zeros(sr + s_offset, dtype=np.float32)  # 1s + s_offset
    e_silence = np.zeros(sr + e_offset, dtype=np.float32)  # 1s + e_offset
    audio = np.concatenate([s_silence, sine_wave, e_silence])

    return audio, sr


def write_wav(filename, audio, sr):
    """Write an audio file in WAV format."""
    with wave.open(filename, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sr)
        wav_file.writeframes(audio.tobytes())


def read_wav(filename):
    """Read an audio file in WAV format."""
    with wave.open(filename, "r") as wav_file:
        sr = wav_file.getframerate()
        audio = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.float32)
    return audio, sr


def test_find_offset_via_cross_correlation():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_offset=24000)

    offset = find_offset_via_cross_correlation(ref_audio, spk_audio)
    assert offset == -24000  # offset should be negative to align the speaker to the reference


def test_shift_audio_s_offset():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_offset=4800)
    shifted = shift_audio(spk_audio, -4800, len(ref_audio))
    assert np.allclose(ref_audio, shifted)


def test_shift_audio_e_offset():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(e_offset=158)
    shifted = shift_audio(spk_audio, 0, len(ref_audio))
    assert len(shifted) == len(ref_audio)
    assert np.allclose(ref_audio, shifted)


def test_shift_audio_both():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(s_offset=800, e_offset=555)
    shifted = shift_audio(spk_audio, -800, len(ref_audio))
    assert len(shifted) == len(ref_audio)
    assert np.allclose(ref_audio, shifted)


def test_align_speaker_to_reference():
    with tempfile.TemporaryDirectory() as temp_dir:
        ref_audio, sr = generate_test_audio()
        spk_audio_0, _ = generate_test_audio(s_offset=4800, e_offset=100)
        spk_audio_1, _ = generate_test_audio(e_offset=800)

        ref_path = os.path.join(temp_dir, "ref.wav")
        spk_path_0 = os.path.join(temp_dir, "spk_0.wav")
        spk_path_1 = os.path.join(temp_dir, "spk_1.wav")

        write_wav(ref_path, ref_audio, sr)
        write_wav(spk_path_0, spk_audio_0, sr)
        write_wav(spk_path_1, spk_audio_1, sr)

        output_path_0 = align_speaker_to_reference(ref_path, spk_path_0, temp_dir)
        output_path_1 = align_speaker_to_reference(ref_path, spk_path_1, temp_dir)

        aligned_audio_0, _ = read_wav(output_path_0)
        aligned_audio_1, _ = read_wav(output_path_1)

        assert len(aligned_audio_0) == len(ref_audio)
        assert len(aligned_audio_1) == len(ref_audio)

        assert np.allclose(ref_audio, aligned_audio_0)
        assert np.allclose(ref_audio, aligned_audio_1)
