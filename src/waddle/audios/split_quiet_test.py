import tempfile
from pathlib import Path

from waddle.audios.split_quiet import split_audio_by_longest_silence

# Define test directory paths
TESTS_DIR_PATH = Path(__file__).resolve().parents[3] / "tests"
EP0_DIR_PATH = TESTS_DIR_PATH / "ep0"


def test_split_audio_by_longest_silence():
    """Test audio splitting by longest silence."""
    wav_file_path = EP0_DIR_PATH / "ep12-shun.wav"
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        temp_wav_path = temp_dir_path / wav_file_path.name
        temp_wav_path.write_bytes(wav_file_path.read_bytes())

        splitted_dir_path = split_audio_by_longest_silence(
            audio_path=temp_wav_path,
            min_ms=2000,
            max_ms=5000,
            silence_thresh=-40,
            min_silence_len=100,
        )
        assert len(list(splitted_dir_path.glob("*.wav"))) > 1, (
            "Should create multiple audio chunks based on silence detection"
        )
