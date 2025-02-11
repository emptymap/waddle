import glob
import os
import sys
import tempfile
import wave
from unittest.mock import patch

import waddle.__main__

dir = os.path.dirname(os.path.abspath(__file__))


def get_wav_duration(filename):
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def run_waddle_command(args):
    with patch.object(sys, "argv", args):
        waddle.__main__.main()


def test_integration_single():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = "ep12-masa.wav"
        input_file_path = os.path.join(dir, "ep0", input_file)

        test_args = ["waddle", "single", input_file_path, "--output", tmpdir]
        run_waddle_command(test_args)

        output_file = os.path.join(tmpdir, input_file)
        assert os.path.exists(output_file), "Output file was not created"

        with wave.open(output_file, "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_preprocess():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "waddle",
            "preprocess",
            "--directory",
            os.path.join(dir, "ep0"),
            "--output",
            tmpdir,
        ]
        run_waddle_command(test_args)

        wav_files = glob.glob(os.path.join(tmpdir, "*.wav"))
        assert len(wav_files) == 3, f"Expected 3 .wav files, but found {len(wav_files)}"

        lengths = [get_wav_duration(wav_file) for wav_file in wav_files]
        assert all(length == lengths[0] for length in lengths[1:]), (
            "Not all processed audio files have the same length"
        )

        reference_file = glob.glob(os.path.join(dir, "ep0", "GMT*"))[0]
        reference_length = get_wav_duration(reference_file)
        assert lengths[0] < reference_length, "Length of processed audio is not less than reference"
