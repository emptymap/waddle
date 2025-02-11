import os
import tempfile
import wave
from unittest import mock

import pytest
from pydub import AudioSegment

from waddle.processing.combine import (
    adjust_pos_to_timeline,
    combine_segments_into_audio,
    merge_timelines,
)


@pytest.fixture
def mock_glob():
    with mock.patch("waddle.processing.combine.glob") as mock_glob:
        mock_glob.return_value = [f"/fake/path/seg_{i}_{i + 100}.wav" for i in range(0, 500, 100)]
        yield mock_glob


@pytest.fixture
def mock_audio_segment():
    with (
        mock.patch.object(AudioSegment, "from_file") as mock_from_file,
        mock.patch.object(AudioSegment, "silent") as mock_silent,
        mock.patch.object(AudioSegment, "overlay") as mock_overlay,
        mock.patch.object(AudioSegment, "export") as mock_export,
    ):
        mock_segment = mock.Mock(spec=AudioSegment)
        mock_from_file.return_value = mock_segment
        mock_silent.return_value = mock_segment
        mock_overlay.return_value = mock_segment
        mock_export.return_value = None  # Export does not return anything

        yield {
            "from_file": mock_from_file,
            "silent": mock_silent,
            "overlay": mock_overlay,
            "export": mock_export,
            "segment": mock_segment,
        }


@pytest.fixture
def mock_os_path():
    with mock.patch("os.path.basename") as mock_basename:
        mock_basename.side_effect = lambda x: os.path.basename(x)  # Returns actual filename
        yield mock_basename


@pytest.fixture
def mock_shutil():
    with mock.patch("shutil.rmtree") as mock_rmtree:
        yield mock_rmtree


@pytest.fixture
def create_dummy_segments():
    with tempfile.TemporaryDirectory() as temp_dir:
        segs_folder = os.path.join(temp_dir, "segments")
        os.makedirs(segs_folder, exist_ok=True)

        for i in range(3):
            AudioSegment.silent(duration=500).export(
                os.path.join(segs_folder, f"chunk_{i * 200}_{(i + 1) * 200}.wav"), format="wav"
            )

        yield segs_folder


def test_combine_segments_into_audio_no_files():
    with tempfile.TemporaryDirectory() as temp_dir:
        segs_folder = os.path.join(temp_dir, "empty_segments")
        os.makedirs(segs_folder, exist_ok=True)
        output_audio = os.path.join(temp_dir, "output.wav")

        combine_segments_into_audio(segs_folder, output_audio)
        assert os.path.exists(output_audio), "Output audio file was not created."

        with wave.open(output_audio, "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_combine_segments_into_audio(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_audio = os.path.join(temp_dir, "output.wav")
        combine_segments_into_audio(create_dummy_segments, output_audio)

        assert os.path.exists(output_audio), "Output audio file was not created."

        with wave.open(output_audio, "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."


def test_merge_timelines_01():
    # separated
    segments = [
        [(0, 100)],
        [(200, 300)],
    ]
    assert merge_timelines(segments) == [(0, 100), (200, 300)]


def test_merge_timelines_02():
    # connected
    segments = [
        [(0, 100)],
        [(100, 200)],
        [(200, 300)],
    ]
    assert merge_timelines(segments) == [(0, 300)]


def test_merge_timelines_03():
    segments = [
        [(0, 100)],
        [(200, 300)],
        [(400, 500)],
    ]
    assert merge_timelines(segments) == [(0, 100), (200, 300), (400, 500)]


def test_merge_timelines_04():
    # overlapping
    segments = [
        [(200, 400)],
        [(0, 300)],
    ]
    assert merge_timelines(segments) == [(0, 400)]


def adjust_pos_to_timeline_01():
    segments = [(0, 100), (200, 300)]
    assert adjust_pos_to_timeline(segments, 0) == 0
    assert adjust_pos_to_timeline(segments, 50) == 50
    assert adjust_pos_to_timeline(segments, 100) == 100
    assert adjust_pos_to_timeline(segments, 150) == 100
    assert adjust_pos_to_timeline(segments, 200) == 100
    assert adjust_pos_to_timeline(segments, 250) == 150
    assert adjust_pos_to_timeline(segments, 300) == 200
    assert adjust_pos_to_timeline(segments, 350) == 200
    assert adjust_pos_to_timeline(segments, 400) == 200


def adjust_pos_to_timeline_02():
    segments = [(100, 300), (400, 500)]
    assert adjust_pos_to_timeline(segments, 100) == 0
    assert adjust_pos_to_timeline(segments, 300) == 200
    assert adjust_pos_to_timeline(segments, 400) == 200
    assert adjust_pos_to_timeline(segments, 450) == 250
    assert adjust_pos_to_timeline(segments, 500) == 300
