import os
import tempfile
import wave
from unittest import mock

import numpy as np
import pytest
from pydub import AudioSegment
from scipy.io import wavfile

from waddle.processing.combine import (
    adjust_pos_to_timeline,
    combine_audio_files,
    combine_segments_into_audio,
    combine_segments_into_audio_with_timeline,
    merge_timelines,
    parse_srt,
)


@pytest.fixture
def mock_glob():
    with mock.patch("waddle.processing.combine.glob") as mock_glob:
        mock_glob.return_value = [f"/fake/path/seg_{i}_{i + 100}.wav" for i in range(0, 500, 100)]
        yield mock_glob


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


def test_combine_segments_into_audio_with_timeline(create_dummy_segments):
    with tempfile.TemporaryDirectory() as temp_dir:
        output_audio = os.path.join(temp_dir, "output.wav")
        timeline = [(0, 100), (150, 250)]
        combine_segments_into_audio_with_timeline(create_dummy_segments, output_audio, timeline)

        assert os.path.exists(output_audio), "Output audio file was not created."


def test_adjust_pos_to_timeline_starting_from_zero():
    """Test adjust_pos_to_timeline where segments start from 0."""
    segments = [(0, 200), (300, 500)]
    assert adjust_pos_to_timeline(segments, 0) == 0, "Boundary adjustment at 0 failed."
    assert adjust_pos_to_timeline(segments, 100) == 100, "Boundary adjustment at 100 failed."
    assert adjust_pos_to_timeline(segments, 199) == 199, "Boundary adjustment at 199 failed."
    assert adjust_pos_to_timeline(segments, 200) == 200, "Boundary adjustment at 200 failed."
    assert adjust_pos_to_timeline(segments, 250) == 200, "Boundary adjustment at 250 failed."
    assert adjust_pos_to_timeline(segments, 300) == 200, "Boundary adjustment at 300 failed."
    assert adjust_pos_to_timeline(segments, 350) == 250, "Boundary adjustment at 350 failed."
    assert adjust_pos_to_timeline(segments, 500) == 400, "Boundary adjustment at 500 failed."


def test_adjust_pos_to_timeline_starting_from_nonzero():
    segments = [(100, 300), (400, 500)]
    assert adjust_pos_to_timeline(segments, 0) == 0, "Boundary adjustment at 0 failed."
    assert adjust_pos_to_timeline(segments, 99) == 0, "Boundary adjustment at 99 failed."
    assert adjust_pos_to_timeline(segments, 100) == 0, "Boundary adjustment at 100 failed."
    assert adjust_pos_to_timeline(segments, 299) == 199, "Boundary adjustment at 299 failed."
    assert adjust_pos_to_timeline(segments, 300) == 200, "Boundary adjustment at 300 failed."
    assert adjust_pos_to_timeline(segments, 350) == 200, "Boundary adjustment at 350 failed."
    assert adjust_pos_to_timeline(segments, 400) == 200, "Boundary adjustment at 400 failed."
    assert adjust_pos_to_timeline(segments, 450) == 250, "Boundary adjustment at 450 failed."
    assert adjust_pos_to_timeline(segments, 500) == 300, "Boundary adjustment at 500 failed."
    assert adjust_pos_to_timeline(segments, 501) == 300, "Boundary adjustment at 501 failed."


def test_combine_audio_files_single_file():
    """Test combining when only a single file exists."""
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_file = os.path.join(temp_dir, "single.wav")
        output_audio = os.path.join(temp_dir, "output.wav")

        AudioSegment.silent(duration=1000).export(audio_file, format="wav")

        combine_audio_files([audio_file], output_audio)

        assert os.path.exists(output_audio), "Output audio file was not created."
        with wave.open(output_audio, "r") as wf:
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
            path = os.path.join(temp_dir, f"segment_{i}.wav")
            wavfile.write(path, sample_rate, segment)
            paths.append(path)

        # Output path for combined audio
        output_audio_path = os.path.join(temp_dir, "combined.wav")

        # Combine audio files
        combine_audio_files(paths, output_audio_path)

        # Read the output audio file
        output_sample_rate, output_audio = wavfile.read(output_audio_path)

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


def test_parse_srt_empty_file():
    """Test parsing an empty SRT file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_file = os.path.join(temp_dir, "empty.srt")
        with open(srt_file, "w") as f:
            f.write("")  # Empty file

        assert parse_srt(srt_file, "Speaker") == [], (
            "Parsing an empty file should return an empty list."
        )


def check_srt_entry(entry: tuple, expected_start: str, expected_end: str, expected_text: str):
    assert entry[0] == expected_start, f"Start time mismatch: {entry[0]} != {expected_start}"
    assert entry[1] == expected_end, f"End time mismatch: {entry[1]} != {expected_end}"
    assert entry[2] == expected_text, f"Text mismatch: {entry[2]} != {expected_text}"


def test_parse_srt_single_entry():
    """Test parsing an SRT file with a single entry."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_file = os.path.join(temp_dir, "single.srt")
        with open(srt_file, "w") as f:
            f.write("1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n")

        entries = parse_srt(srt_file, "Speaker")
        assert len(entries) == 1, "Single entry should be parsed."

        check_srt_entry(entries[0], "00:00:00.000", "00:00:05.000", "Speaker: Hello world.")


def test_parse_srt_multiple_entries():
    """Test parsing an SRT file with multiple entries."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srt_file = os.path.join(temp_dir, "multiple.srt")
        with open(srt_file, "w") as f:
            f.write(
                "1\n00:00:00,000 --> 00:00:05,000\nHello world.\n\n"
                "2\n00:00:05,000 --> 00:00:10,000\nHow are you?\n\n"
                "3\n00:00:10,000 --> 00:00:15,000\nI'm fine, thanks.\n\n"
            )

        entries = parse_srt(srt_file, "Speaker")
        assert len(entries) == 3, "Three entries should be parsed."

        check_srt_entry(entries[0], "00:00:00.000", "00:00:05.000", "Speaker: Hello world.")
        check_srt_entry(entries[1], "00:00:05.000", "00:00:10.000", "Speaker: How are you?")
        check_srt_entry(entries[2], "00:00:10.000", "00:00:15.000", "Speaker: I'm fine, thanks.")


def test_merge_timelines_separated_segments():
    """Test merging timelines where segments are completely separate."""
    segments = [
        [(0, 100)],
        [(200, 300)],
    ]
    expected = [(0, 100), (200, 300)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_continuous_segments():
    """Test merging timelines where segments are directly connected."""
    segments = [
        [(0, 100)],
        [(100, 200)],
        [(200, 300)],
    ]
    expected = [(0, 300)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_non_overlapping_segments():
    """Test merging timelines with non-overlapping segments."""
    segments = [
        [(0, 100)],
        [(200, 300)],
        [(400, 500)],
    ]
    expected = [(0, 100), (200, 300), (400, 500)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"


def test_merge_timelines_overlapping_segments():
    """Test merging timelines where segments overlap."""
    segments = [
        [(200, 400)],
        [(0, 300)],
    ]
    expected = [(0, 400)]
    result = merge_timelines(segments)
    assert result == expected, f"Expected {expected}, but got {result}"
