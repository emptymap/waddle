import tempfile
import wave
from pathlib import Path

from waddle.audios.clip import clip_audio

TESTS_DIR_PATH = Path(__file__).resolve().parent.parents[2] / "tests"
EP0_DIR_PATH = TESTS_DIR_PATH / "ep0"


def get_wav_duration(filename):
    """Returns the duration of a WAV file."""
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def test_clip_audio_01():
    with tempfile.NamedTemporaryFile() as temp_file:
        clip_audio(EP0_DIR_PATH / "ep12-masa.wav", Path(temp_file.name), 0, 10)
        assert get_wav_duration(temp_file.name) == 10  # 10 seconds


def test_clip_audio_02():
    with tempfile.NamedTemporaryFile() as temp_file:
        clip_audio(EP0_DIR_PATH / "ep12-masa.wav", Path(temp_file.name), 0, 30)
        assert (
            14 <= get_wav_duration(temp_file.name) <= 15
        )  # Should match the original length (14.052s)


def test_clip_audio_03():
    with tempfile.NamedTemporaryFile() as temp_file:
        clip_audio(EP0_DIR_PATH / "ep12-masa.wav", Path(temp_file.name), 5, 30)
        assert (
            9 <= get_wav_duration(temp_file.name) <= 10
        )  # should be original length (14.052) - 5 seconds


def test_clip_audio_04():
    with tempfile.NamedTemporaryFile() as temp_file:
        clip_audio(EP0_DIR_PATH / "ep12-masa.wav", Path(temp_file.name), 5)
        assert 9 <= get_wav_duration(temp_file.name) <= 10  # same as above
