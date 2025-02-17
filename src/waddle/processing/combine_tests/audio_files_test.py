import tempfile
import wave
from pathlib import Path

import numpy as np
from pydub import AudioSegment
from scipy.io import wavfile

from waddle.processing.combine import (
    combine_audio_files,
)


def test_combine_audio_files_single_file():
    """Test combining when only a single file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        audio_file = temp_dir / "single.wav"
        output_audio = temp_dir / "output.wav"

        AudioSegment.silent(duration=1000).export(str(audio_file), format="wav")

        combine_audio_files([audio_file], output_audio)

        assert output_audio.exists(), "Output audio file was not created."
        with wave.open(str(output_audio), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def generate_sine_wave(frequency=440, duration_ms=500, sample_rate=44100, amplitude=0.5):
    """
    Generate a NumPy array representing a sine wave.
    """
    t = np.linspace(0, duration_ms / 1000, int(sample_rate * (duration_ms / 1000)), endpoint=False)
    waveform = (amplitude * np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    return waveform


def test_combine_audio_files_with_numpy_verification():
    """
    Test combining three different sine wave audio segments and verify output using NumPy.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        sample_rate = 44100
        duration_ms = 500  # 500ms per segment

        # Generate three different sine wave signals
        segment1 = generate_sine_wave(
            frequency=440, duration_ms=duration_ms, sample_rate=sample_rate
        )
        segment2 = generate_sine_wave(
            frequency=880, duration_ms=duration_ms, sample_rate=sample_rate
        )
        segment3 = generate_sine_wave(
            frequency=1760, duration_ms=duration_ms, sample_rate=sample_rate
        )

        # Save the three segments as separate WAV files
        paths = []
        for i, segment in enumerate([segment1, segment2, segment3]):
            path = temp_dir / f"segment_{i}.wav"
            wavfile.write(str(path), sample_rate, segment)
            paths.append(str(path))

        # Output path for combined audio
        output_audio_path = temp_dir / "combined.wav"

        # Combine audio files
        combine_audio_files(paths, output_audio_path)

        # Read the output audio file
        output_sample_rate, output_audio = wavfile.read(str(output_audio_path))

        # Ensure the sample rate is unchanged
        assert output_sample_rate == sample_rate, "Sample rate mismatch in output audio."

        # Expected output: Element-wise sum of the three signals
        expected_audio = (
            segment1.astype(np.int32) + segment2.astype(np.int32) + segment3.astype(np.int32)
        )

        # Prevent overflow by clipping to int16 range
        expected_audio = np.clip(expected_audio, -32768, 32767).astype(np.int16)

        # Compare the actual combined audio with the expected sum
        np.testing.assert_array_equal(
            output_audio, expected_audio, "Combined audio does not match expected waveform."
        )
