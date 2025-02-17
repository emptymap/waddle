from pathlib import Path

import librosa
import numpy as np

from waddle.audios.audio_io import read_wave

# Define test directory paths
TESTS_DIR_PATH = Path(__file__).resolve().parent.parents[2] / "tests"
EP0_DIR_PATH = TESTS_DIR_PATH / "ep0"


def test_read_file():
    # Read the first 5 seconds of the first audio file
    file_path = EP0_DIR_PATH / "ep12-masa.wav"
    audio, sr = read_wave(file_path, duration=1)

    # Check the audio data and sample rate
    assert len(audio) == 1 * sr
    assert sr == 48000

    # Compare to librosa
    ref_audio, ref_sr = librosa.load(file_path, sr=sr, mono=True, duration=1)
    assert len(audio) == len(ref_audio)
    assert np.allclose(audio, ref_audio)
