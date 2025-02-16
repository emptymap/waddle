import subprocess
import tempfile
import wave
from pathlib import Path
from unittest.mock import patch

import pytest

from waddle.audios.call_tools import (
    convert_to_wav,
    ensure_sampling_rate,
    remove_noise,
    transcribe,
)

# Define test directory paths
TESTS_DIR = Path(__file__).resolve().parent.parents[2] / "tests"
EP0_DIR = TESTS_DIR / "ep0"


def get_wav_duration(file_path: Path) -> float:
    """Returns the duration of a WAV file."""
    with wave.open(str(file_path), "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        return frames / float(rate)


def test_convert_to_wav():
    """Test that `.m4a` files are converted to `.wav` format."""
    m4a_file = EP0_DIR / "ep12-masa.m4a"
    if not m4a_file.exists():
        pytest.skip(f"Sample file {m4a_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_m4a = temp_dir_path / m4a_file.name
        temp_m4a.write_bytes(m4a_file.read_bytes())  # Copy file using pathlib

        convert_to_wav(temp_dir_path)

        expected_output = temp_m4a.with_suffix(".wav")
        assert expected_output.exists()


def test_convert_to_wav_existing_wav():
    """Test when `.m4a` exists but corresponding `.wav` is already present."""
    m4a_file = EP0_DIR / "ep12-masa.m4a"
    wav_file = EP0_DIR / "ep12-masa.wav"

    if not m4a_file.exists() or not wav_file.exists():
        pytest.skip(f"Sample files {m4a_file} or {wav_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_m4a = temp_dir_path / m4a_file.name
        temp_wav = temp_dir_path / wav_file.name
        temp_m4a.write_bytes(m4a_file.read_bytes())  # Copy .m4a
        temp_wav.write_bytes(wav_file.read_bytes())  # Copy .wav (same name)

        with patch("builtins.print") as mock_print:
            convert_to_wav(temp_dir_path)

            # Ensure `[INFO]` message is printed when skipping `.m4a`
            assert any("[INFO] Skipping" in call.args[0] for call in mock_print.call_args_list)

        # Since .wav already exists, .m4a should be skipped (not overwritten)
        assert temp_wav.exists()


def test_convert_to_wav_error():
    """
    Test that `subprocess.CalledProcessError` is handled in convert_to_wav,
    ensuring `[ERROR]` is printed.
    """
    m4a_file = EP0_DIR / "ep12-masa.m4a"
    if not m4a_file.exists():
        pytest.skip(f"Sample file {m4a_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_m4a = temp_dir_path / m4a_file.name
        temp_m4a.write_bytes(m4a_file.read_bytes())  # Copy file

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with pytest.raises(RuntimeError, match="Converting"):
                convert_to_wav(temp_dir_path)


def test_ensure_sampling_rate():
    """Test that the sampling rate is correctly set."""
    wav_file = EP0_DIR / "ep12-masa.wav"
    if not wav_file.exists():
        pytest.skip(f"Sample file {wav_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav = temp_dir_path / wav_file.name
        temp_wav.write_bytes(wav_file.read_bytes())  # Copy file

        output_wav = temp_dir_path / "output.wav"
        ensure_sampling_rate(temp_wav, output_wav, target_rate=16000)

        assert output_wav.exists()
        assert get_wav_duration(output_wav) == pytest.approx(get_wav_duration(temp_wav), rel=0.1)


def test_ensure_sampling_rate_file_not_found():
    """Test `ensure_sampling_rate` when input file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        fake_input = temp_dir_path / "non_existent.wav"
        output_wav = temp_dir_path / "output.wav"

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            ensure_sampling_rate(fake_input, output_wav, target_rate=16000)


def test_ensure_sampling_rate_error():
    """Test that `subprocess.CalledProcessError` is handled in ensure_sampling_rate, ensuring `[ERROR]` is printed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        fake_input = temp_dir_path / "input.wav"
        output_wav = temp_dir_path / "output.wav"

        # Create an empty input file
        fake_input.touch()

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "ffmpeg")):
            with pytest.raises(RuntimeError, match="Converting"):
                ensure_sampling_rate(fake_input, output_wav, target_rate=16000)


def test_remove_noise():
    """Test noise removal function."""
    wav_file = EP0_DIR / "ep12-masa.wav"
    if not wav_file.exists():
        pytest.skip(f"Sample file {wav_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav = temp_dir_path / wav_file.name
        temp_wav.write_bytes(wav_file.read_bytes())  # Copy file

        output_wav = temp_dir_path / "output.wav"
        try:
            remove_noise(temp_wav, output_wav)
            assert output_wav.exists()
        except FileNotFoundError:
            pytest.skip("DeepFilterNet tool not installed")


def test_transcribe():
    """Test Whisper transcription function."""
    wav_file = EP0_DIR / "ep12-masa.wav"
    if not wav_file.exists():
        pytest.skip(f"Sample file {wav_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav = temp_dir_path / wav_file.name
        temp_wav.write_bytes(wav_file.read_bytes())  # Copy file

        output_srt = temp_dir_path / "output.srt"
        try:
            transcribe(temp_wav, output_srt, language="ja")
            assert output_srt.exists()
            # Check line is more than 3
            assert len(output_srt.read_text().strip().split("\n")) > 3
        except FileNotFoundError:
            pytest.skip("Whisper CLI or model not installed")
