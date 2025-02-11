import glob
import os
import tempfile
import wave

import waddle
import waddle.__main__
import waddle.argparse

dir = os.path.dirname(os.path.abspath(__file__))


def get_wav_duration(filename):
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def test_integration_single():
    parser = waddle.argparse.create_waddle_parser()
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = "ep12-masa.wav"
        input_file_path = os.path.join(dir, "ep0", input_file)

        args = parser.parse_args(["single", input_file_path, "--output", tmpdir])
        waddle.__main__.do_single(args)

        output_file = os.path.join(tmpdir, input_file)
        assert os.path.exists(output_file), "Output file was not created"

        with wave.open(output_file, "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_preprocess():
    parser = waddle.argparse.create_waddle_parser()
    with tempfile.TemporaryDirectory() as tmpdir:
        args = parser.parse_args(
            ["preprocess", "--directory", os.path.join(dir, "ep0"), "--output", tmpdir]
        )
        waddle.__main__.do_preprocess(args)
        wav_files = glob.glob(os.path.join(tmpdir, "*.wav"))
        assert len(wav_files) == 3, f"Expected 3 .wav files, but found {len(wav_files)}"

        lengths = list()
        for wav_file in wav_files:
            lengths.append(get_wav_duration(wav_file))
        assert all(length == lengths[0] for length in lengths[1:]), (
            "Not all processed audio files have the same length"
        )

        reference_file = glob.glob(os.path.join(dir, "ep0", "GMT*"))[0]
        reference_length = get_wav_duration(reference_file)
        assert lengths[0] < reference_length, "Length of processed audio is not less than reference"
