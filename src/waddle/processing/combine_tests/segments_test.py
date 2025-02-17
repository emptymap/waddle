import tempfile
import wave
from pathlib import Path

import pytest
from pydub import AudioSegment

from waddle.processing.combine import (
    combine_segments_into_audio,
    combine_segments_into_audio_with_timeline,
)
from waddle.utils import format_audio_filename


@pytest.fixture
def create_dummy_segments():
    def _create_dummy_segments(timeline):
        temp_dir = tempfile.TemporaryDirectory()
        segs_folder = Path(temp_dir.name) / "segments"
        segs_folder.mkdir(parents=True, exist_ok=True)

        for start, end in timeline:
            duration_ms = end - start
            AudioSegment.silent(duration=duration_ms).export(
                segs_folder / format_audio_filename("seg", start, end),
                format="wav",
            )
        return segs_folder

    return _create_dummy_segments


def test_combine_segments_into_audio_no_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        segs_folder = temp_dir_path / "empty_segments"
        segs_folder.mkdir(parents=True, exist_ok=True)
        output_audio_path = temp_dir_path / "output.wav"

        combine_segments_into_audio(segs_folder, output_audio_path)
        assert output_audio_path.exists(), "Output audio file was not created."

        with wave.open(str(output_audio_path), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250), (250, 299)]
        segs_folder = create_dummy_segments(timeline)
        combine_segments_into_audio(segs_folder, output_audio_path)

        assert output_audio_path.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio_extra_segment(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(100, 200), (200, 350), (501, 555)]
        segs_folder = create_dummy_segments(timeline)
        combine_segments_into_audio(segs_folder, output_audio_path)

        assert output_audio_path.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio_with_timeline(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250), (250, 299)]
        segs_folder = create_dummy_segments(timeline)
        combine_segments_into_audio_with_timeline(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio_with_timeline_extra_segment(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(100, 200), (200, 350), (501, 555)]
        segs_folder = create_dummy_segments(timeline)
        combine_segments_into_audio_with_timeline(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio_with_timeline_no_files():
    """Test handling of an empty segment folder in combine_segments_into_audio_with_timeline."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        segs_folder = temp_dir_path / "empty_segments"
        segs_folder.mkdir(parents=True, exist_ok=True)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250)]

        combine_segments_into_audio_with_timeline(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), (
            "Output silent audio file should be created when no segments are available."
        )
