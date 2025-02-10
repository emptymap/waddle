import wave
import waddle
import os
import waddle.argparse
import waddle.__main__
import tempfile
import glob

dir = os.path.dirname(os.path.abspath(__file__))


def get_wav_duration(filename):
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


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
        assert all(
            length == lengths[0] for length in lengths[1:]
        ), "Not all processed audio files have the same length"

        reference_file = glob.glob(os.path.join(dir, "ep0", "GMT*"))[0]
        reference_length = get_wav_duration(reference_file)
        assert (
            lengths[0] < reference_length
        ), "Length of processed audio is not less than reference"
