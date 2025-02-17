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
    with wave.open(str(file_path), "r") as wav_file_path:
        frames = wav_file_path.getnframes()
        rate = wav_file_path.getframerate()
        return frames / float(rate)


def get_total_noise_amount(file_path: Path, threshold: int = 150) -> float:
    """Returns the total amount of noise in a WAV file."""
    with wave.open(str(file_path), "r") as wav_file_path:
        n_channels = wav_file_path.getnchannels()
        n_frames = wav_file_path.getnframes()
        audio_data = wav_file_path.readframes(n_frames)

        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        audio_array = np.abs(audio_array)

        if n_channels > 1:
            audio_array = audio_array.reshape(-1, n_channels).mean(axis=1)

        noise_amount = np.sum(audio_array[audio_array < threshold])
        return noise_amount


def test_convert_to_wav():
    """Test that `.m4a` files are converted to `.wav` format."""
    m4a_file = EP0_DIR_PATH / "ep12-masa.m4a"
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
    m4a_file = EP0_DIR_PATH / "ep12-masa.m4a"
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"

    if not m4a_file.exists() or not wav_file_path.exists():
        pytest.skip(f"Sample files {m4a_file} or {wav_file_path} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_m4a = temp_dir_path / m4a_file.name
        temp_wav_path = temp_dir_path / wav_file_path.name
        temp_m4a.write_bytes(m4a_file.read_bytes())  # Copy .m4a
        temp_wav_path.write_bytes(wav_file_path.read_bytes())  # Copy .wav (same name)

        with patch("builtins.print") as mock_print:
            convert_to_wav(temp_dir_path)

            # Ensure `[INFO]` message is printed when skipping `.m4a`
            assert any("[INFO] Skipping" in call.args[0] for call in mock_print.call_args_list)

        # Since .wav already exists, .m4a should be skipped (not overwritten)
        assert temp_wav_path.exists()


def test_convert_to_wav_error():
    """Test when an error occurs during conversion."""
    m4a_file = EP0_DIR_PATH / "ep12-masa.m4a"
    if not m4a_file.exists():
        pytest.skip(f"Sample file {m4a_file} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_m4a = temp_dir_path / m4a_file.name
        temp_m4a.write_bytes(m4a_file.read_bytes())  # Copy file

        with subprocess_run_with_error("ffmpeg"):
            with pytest.raises(RuntimeError, match="Converting"):
                convert_to_wav(temp_dir_path)


def test_ensure_sampling_rate():
    """Test that the sampling rate is correctly set."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"
    if not wav_file_path.exists():
        pytest.skip(f"Sample file {wav_file_path} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav_path = temp_dir_path / wav_file_path.name
        temp_wav_path.write_bytes(wav_file_path.read_bytes())  # Copy file

        output_wav = temp_dir_path / "output.wav"
        ensure_sampling_rate(temp_wav_path, output_wav, target_rate=16000)

        assert output_wav.exists()
        assert get_wav_duration(output_wav) == pytest.approx(
            get_wav_duration(temp_wav_path), rel=0.1
        )


def test_ensure_sampling_rate_file_not_found():
    """Test `ensure_sampling_rate` when input file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        fake_input = temp_dir_path / "non_existent.wav"
        output_wav = temp_dir_path / "output.wav"

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            ensure_sampling_rate(fake_input, output_wav, target_rate=16000)


def test_ensure_sampling_rate_error():
    """Test `ensure_sampling_rate` when an error occurs during conversion."""
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
    """Test noise removal using DeepFilterNet."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"
    if not wav_file_path.exists():
        pytest.skip(f"Sample file {wav_file_path} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav_path = temp_dir_path / wav_file_path.name
        temp_wav_path.write_bytes(wav_file_path.read_bytes())

        output_wav = temp_dir_path / "denoised.wav"

        remove_noise(temp_wav_path, output_wav)

        assert output_wav.exists()
        assert get_wav_duration(output_wav) == pytest.approx(
            get_wav_duration(temp_wav_path), rel=0.1
        )
        assert output_wav.read_bytes() != temp_wav_path.read_bytes()

        # To compare noise levels, ensure_sampling_rate is used to convert to 48kHz
        temp_wav_path_48k = temp_dir_path / "temp_48k.wav"
        ensure_sampling_rate(temp_wav_path, temp_wav_path_48k, target_rate=48000)
        assert get_total_noise_amount(output_wav) < get_total_noise_amount(temp_wav_path_48k), (
            "Noise not removed"
        )


def test_remove_noise_same_output_path():
    """Test noise removal when input and output paths are the same."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"
    if not wav_file_path.exists():
        pytest.skip(f"Sample file {wav_file_path} not found")

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
    """Test transcription using Whisper."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"
    if not wav_file_path.exists():
        pytest.skip(f"Sample file {wav_file_path} not found")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav_path = temp_dir_path / wav_file_path.name
        temp_wav_path.write_bytes(wav_file_path.read_bytes())

        output_txt = temp_dir_path / "transcription.txt"

        transcribe(temp_wav_path, output_txt)

        assert output_txt.exists()
        assert len(output_txt.read_text().strip().split("\n")) > 3


def test_transcribe_file_not_found():
    """Test transcribe when input file does not exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        fake_input = temp_dir_path / "non_existent.wav"
        output_txt = temp_dir_path / "transcription.txt"

        with pytest.raises(FileNotFoundError, match="Input file not found"):
            transcribe(fake_input, output_txt)


def test_transcribe_error():
    """Test transcribe when subprocess raises an error."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"
    if not wav_file_path.exists():
        pytest.skip(f"Sample file {wav_file_path} not found")

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
