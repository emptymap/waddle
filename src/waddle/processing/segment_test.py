import tempfile
import wave
from pathlib import Path

import pytest

from waddle.processing.segment import SegmentsProcessor

TESTS_DIR_PATH = Path(__file__).resolve().parent.parents[2] / "tests"
EP0_DIR_PATH = TESTS_DIR_PATH / "ep0"


def get_wav_duration(filename):
    """Returns the duration of a WAV file."""
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def test_merge_raw_timeline_01():
    segments = [(0, 100), (200, 300)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 100), (200, 300)]


def test_merge_raw_timeline_02():
    segments = [(0, 100), (100, 200), (200, 300)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 300)]


def test_merge_raw_timeline_03():
    segments = [(0, 300), (200, 400), (500, 600)]
    assert SegmentsProcessor._merge_raw_timeline(segments) == [(0, 400), (500, 600)]


def test_merge_raw_timeline_04():
    segments = []
    assert SegmentsProcessor._merge_raw_timeline(segments) == []


def test_segs_processor():
    with tempfile.TemporaryDirectory() as temp_dir:
        aligned_audio_path = Path(temp_dir) / "ep12-masa.wav"
        aligned_audio_path.write_bytes((EP0_DIR_PATH / "ep12-masa.wav").read_bytes())

        segs_processor = SegmentsProcessor.from_audio(aligned_audio_path)
        assert segs_processor is not None
        assert segs_processor.segs_dir_path.exists()
        assert len(list(segs_processor.segs_dir_path.glob("*.wav"))) > 0


def test_segs_processor_no_exist():
    with tempfile.TemporaryDirectory() as temp_dir:
        # check FileNotFoundError
        pytest.raises(
            FileNotFoundError, SegmentsProcessor.from_audio, Path(temp_dir) / "non-existent.wav"
        )


def test_segs_processor_no_segs():
    with tempfile.TemporaryDirectory() as temp_dir:
        aligned_audio_path = Path(temp_dir) / "ep12-masa.wav"
        aligned_audio_path.write_bytes((EP0_DIR_PATH / "ep12-masa.wav").read_bytes())

        segs_processor = SegmentsProcessor.from_audio(aligned_audio_path, threshold_db=999)
        assert segs_processor is not None
        assert segs_processor.segs_dir_path.exists()
        assert len(list(segs_processor.segs_dir_path.glob("*.wav"))) == 0
