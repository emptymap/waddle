import tempfile
import wave
from pathlib import Path

import pytest
from pydub import AudioSegment

from waddle.processing.combine import (
    combine_segments_into_audio,
)
from waddle.utils import format_audio_filename


def create_dummy_segments(dir_path, timeline):
    segs_folder = dir_path / "segments"
    segs_folder.mkdir(parents=True, exist_ok=True)

    for start, end in timeline:
        duration_ms = end - start
        AudioSegment.silent(duration=duration_ms).export(
            segs_folder / format_audio_filename("seg", start, end),
            format="wav",
        )
    return segs_folder


def get_wav_duration(filename):
    """Returns the duration of a WAV file."""
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


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


def test_combine_segments_into_audio():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250), (250, 299)]
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        combine_segments_into_audio(segs_folder, output_audio_path)

        assert output_audio_path.exists(), "Output audio file was not created."
        assert pytest.approx(get_wav_duration(str(output_audio_path)), 0.001) == 299 / 1000


def test_combine_segments_into_audio_extra_segment():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(100, 200), (200, 350), (501, 555)]
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        combine_segments_into_audio(segs_folder, output_audio_path)

        assert output_audio_path.exists(), "Output audio file was not created."
        assert pytest.approx(get_wav_duration(str(output_audio_path)), 0.001) == 555 / 1000


def test_combine_segments_into_audio_with_timeline():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250), (250, 299)]
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        combine_segments_into_audio(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), "Output audio file was not created."
        assert (
            pytest.approx(get_wav_duration(str(output_audio_path)), 0.001)
            == (100 + 100 + 49) / 1000
        )


def test_combine_segments_into_audio_extra_segment_with_timeline():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(100, 200), (200, 350), (501, 555)]
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        combine_segments_into_audio(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), "Output audio file was not created."
        assert (
            pytest.approx(get_wav_duration(str(output_audio_path)), 0.001)
            == (100 + 150 + 54) / 1000
        )


def test_combine_segments_into_audio_no_files_with_timeline():
    """Test handling of an empty segment folder in combine_segments_into_audio."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        segs_folder = temp_dir_path / "empty_segments"
        segs_folder.mkdir(parents=True, exist_ok=True)
        output_audio_path = temp_dir_path / "output.wav"
        timeline = [(0, 100), (150, 250)]

        combine_segments_into_audio(segs_folder, output_audio_path, timeline)

        assert output_audio_path.exists(), (
            "Output silent audio file should be created when no segments are available."
        )


def test_compare_two_combine_segments():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        output_audio_path_0 = temp_dir_path / "output_0.wav"
        timeline = [(0, 100), (150, 250), (250, 299)]
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        combine_segments_into_audio(segs_folder, output_audio_path_0)

        assert output_audio_path_0.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path_0), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."

        output_audio_path_1 = temp_dir_path / "output_1.wav"
        segs_folder = create_dummy_segments(temp_dir_path, timeline)
        new_timeline = [(timeline[0][0], timeline[-1][1])]
        combine_segments_into_audio(segs_folder, output_audio_path_1, new_timeline)

        assert output_audio_path_1.exists(), "Output audio file was not created."
        with wave.open(str(output_audio_path_1), "r") as wf:
            assert wf.getnframes() > 0, "Output audio file is empty."

        assert pytest.approx(get_wav_duration(str(output_audio_path_0)), 0.001) == get_wav_duration(
            str(output_audio_path_1)
        )
