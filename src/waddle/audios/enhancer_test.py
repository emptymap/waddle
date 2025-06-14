from pathlib import Path

from pydub import AudioSegment

from waddle.audios.enhancer import enhance_audio_quality

# Define test directory paths
TESTS_DIR_PATH = Path(__file__).resolve().parents[3] / "tests"
EP0_DIR_PATH = TESTS_DIR_PATH / "ep0"


def test_enhance_audio_quality():
    """Test audio enhancement using DeepFilterNet."""
    wav_file_path = EP0_DIR_PATH / "ep12-masa.wav"

    audio = AudioSegment.from_file(wav_file_path)
    enhanced_audio = enhance_audio_quality(audio)
    assert audio.rms != enhanced_audio.rms, "Audio should be enhanced"
