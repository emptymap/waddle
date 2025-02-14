import os
import tempfile
import wave

import matplotlib.pyplot as plt
import numpy as np

from waddle.audios.align_offset import (
    align_speaker_to_reference,
    find_offset_via_cross_correlation,
    shift_audio,
)


def generate_test_audio(sr=48000, offset=0):
    """Generate a test sine wave audio signal with 1s silence, 1s sine wave, and 1s silence."""
    t = np.linspace(0, np.pi / 2, int(sr * 1.0), endpoint=False)
    sine_wave = (32767 * 0.5 * np.sin(t)).astype(np.float32)
    silence = np.zeros(int(sr * 1.0), dtype=np.float32)
    audio = np.concatenate([silence, sine_wave, silence])

    if offset > 0:
        audio = np.pad(audio, (offset, 0), mode="constant", constant_values=0)
    elif offset < 0:
        audio = np.pad(audio, (0, abs(offset)), mode="constant", constant_values=0)

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
        audio = np.frombuffer(wav_file.readframes(wav_file.getnframes()), dtype=np.int16)
    return audio, sr


def plot_waveform(audio, sr, title="waveform"):
    """Plot the waveform of an audio signal."""
    time_axis = np.linspace(0, len(audio) / sr, num=len(audio))
    plt.figure(figsize=(10, 4))
    plt.plot(time_axis, audio, label="Audio Signal")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.title(title)
    plt.legend()
    plt.grid()
    plt.savefig(f"{title}.png")


def test_find_offset_via_cross_correlation():
    ref_audio, sr = generate_test_audio()
    spk_audio, _ = generate_test_audio(offset=24000)  # 500ms offset at 48kHz
    plot_waveform(ref_audio, sr, title="Reference Audio Signal")
    plot_waveform(spk_audio, sr, title="Speaker Audio Signal")
    offset = find_offset_via_cross_correlation(ref_audio, spk_audio)  # offset should be -4800
    assert abs(offset + 24000) < 100  # Allowable error for 100Hz (0.625ms at 48kHz)


def test_shift_audio():
    ref_audio, _ = generate_test_audio()
    spk_audio, _ = generate_test_audio(offset=-24000)
    shifted = shift_audio(spk_audio, 4800, len(ref_audio))
    assert np.allclose(ref_audio, shifted)


def test_align_speaker_to_reference():
    with tempfile.TemporaryDirectory() as temp_dir:
        ref_audio, sr = generate_test_audio()
        spk_audio_0, _ = generate_test_audio(offset=4800)
        spk_audio_1, _ = generate_test_audio(offset=-4800)

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
