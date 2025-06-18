import subprocess
import sys
import tempfile
import wave
from pathlib import Path

dir = Path(__file__).resolve().parent


def run_waddle_command(args):
    """Runs the waddle command using subprocess and captures the output."""
    result = subprocess.run(
        [sys.executable, "-m", "waddle"] + args,
        capture_output=True,
        text=True,
    )
    return result


def get_wav_duration(filename):
    """Returns the duration of a WAV file."""
    with wave.open(filename, "r") as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def test_integration_single():
    """Tests single file processing in Waddle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = "ep12-masa.wav"
        input_file_path = dir / "ep0" / input_file
        tmpdir_path = Path(tmpdir)

        test_args = ["single", str(input_file_path), "--output", tmpdir]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        output_file = tmpdir_path / input_file
        assert output_file.exists(), "Output file was not created"

        with wave.open(str(output_file), "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_single_file_not_found():
    """Tests handling of a missing input file by checking the expected FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file_path = dir / "ep0" / "non_existent.wav"

        test_args = ["single", str(input_file_path), "--output", tmpdir]
        result = run_waddle_command(test_args)

        # Ensure that the command fails
        assert result.returncode != 0, "Command should fail for missing file"

        # Ensure that the error message contains 'Audio file not found'
        expected_error_message = f"Audio file not found: {input_file_path}"
        assert expected_error_message in result.stderr, (
            f"Expected '{expected_error_message}' not found in stderr:\n{result.stderr}"
        )


def test_integration_single_m4a():
    """Tests single file processing with an M4A file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file = "ep12-masa.m4a"
        input_file_path = dir / "ep0" / input_file
        tmpdir_path = Path(tmpdir)

        test_args = ["single", str(input_file_path), "--output", str(tmpdir), "-ss", "5", "-t", "5"]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        output_file = tmpdir_path / input_file.replace(".m4a", ".wav")
        assert output_file.exists(), "Output file was not created"

        with wave.open(str(output_file), "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_preprocess():
    """Tests the preprocess command for batch processing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_args = [
            "preprocess",
            "--directory",
            str(dir / "ep0"),
            "--output",
            tmpdir,
            "-ss",
            "5",
            "-t",
            "5",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        wav_files = list(tmpdir_path.glob("*.wav"))
        assert len(wav_files) == 3, f"Expected 3 .wav files, but found {len(wav_files)}"

        lengths = [get_wav_duration(str(wav_file)) for wav_file in wav_files]
        assert all(length == lengths[0] for length in lengths[1:]), (
            "Not all processed audio files have the same length"
        )

        reference_file = list((dir / "ep0").glob("GMT*"))[0]
        reference_length = get_wav_duration(str(reference_file))
        assert lengths[0] < reference_length, "Length of processed audio is not less than reference"

        # Check transcription files (should NOT be created)
        srt_files = list(tmpdir_path.glob("*.srt"))
        assert len(srt_files) == 0, f"Expected 0 SRT files, but found {len(srt_files)}"


def test_integration_preprocess_transcribe():
    """Tests the preprocess command with transcription disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_args = [
            "preprocess",
            "--directory",
            str(dir / "ep0"),
            "--output",
            tmpdir,
            "-ss",
            "5",
            "-t",
            "5",
            "--transcribe",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        # Check WAV files (should still be created)
        wav_files = list(tmpdir_path.glob("*.wav"))
        assert len(wav_files) == 3, f"Expected 3 .wav files, but found {len(wav_files)}"

        # Check transcription files
        srt_files = list(tmpdir_path.glob("*.srt"))
        assert len(srt_files) == 1, f"Expected 1 SRT file, but found {len(srt_files)}"
        with Path(srt_files[0]).open("r", encoding="utf-8") as f:
            content = f.read()
            assert len(content) > 0, f"SRT file {srt_files[0]} is empty"


def test_integration_preprocess_no_reference():
    """Tests the preprocess command without a reference file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "preprocess",
            "--directory",
            str(dir / "ep0"),
            "--reference",
            "non_existent.wav",
            "--output",
            tmpdir,
            "-ss",
            "5",
            "-t",
            "5",
            "--no-convert",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode != 0, "Command should fail without a reference file"


def test_integration_preprocess_no_source_dir():
    """Tests the preprocess command without a source directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "preprocess",
            "--directory",
            "non_existent",
            "--output",
            tmpdir,
            "-ss",
            "5",
            "-t",
            "5",
            "--no-convert",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode != 0, "Command should fail without a source directory"


def test_integration_postprocess():
    """Tests the postprocess command for batch processing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_args = [
            "postprocess",
            "--directory",
            str(dir / "ep0"),
            "--output",
            tmpdir,
            "-ss",
            "10",
            "-t",
            "6",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        wav_files = list(tmpdir_path.glob("*.wav"))
        assert len(wav_files) == 4, f"Expected 4 .wav files, but found {len(wav_files)}"
        assert get_wav_duration(str(wav_files[0])) < 6, "Output audio file has incorrect duration"

        srt_files = list(tmpdir_path.glob("*.srt"))
        assert len(srt_files) == 1, f"Expected 1 .srt file, but found {len(srt_files)}"


def test_integration_postprocess_no_source_dir():
    """Tests the postprocess command without a source directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "postprocess",
            "--directory",
            "non_existent",
            "--output",
            tmpdir,
        ]
        result = run_waddle_command(test_args)

        assert result.returncode != 0, "Command should fail without a source directory"


def test_integration_metadata():
    """Tests the metadata command for generating metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_args = [
            "metadata",
            str(dir / "ep0" / "ep12.md"),
            "--input",
            str(dir / "ep0" / "ep12-masa.wav"),
            "--output",
            tmpdir,
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        files = list(tmpdir_path.iterdir())
        print("Files in temporary directory:", files)

        mp3_file = tmpdir_path / "ep12-masa.mp3"
        assert mp3_file.exists(), "MP3 file was not created"

        chapters_file = tmpdir_path / "ep12.chapters.txt"
        assert chapters_file.exists(), "Chapters file was not created"

        show_notes_file = tmpdir_path / "ep12.show_notes.md"
        assert show_notes_file.exists(), "Show notes file was not created"


def test_integration_install():
    """Tests the install command for installing all tools."""
    test_args = ["install"]
    result = run_waddle_command(test_args)

    assert result.returncode == 0, f"Install command failed with error: {result.stderr}"

    # Check that install output contains expected messages
    assert "Installing all required tools for waddle..." in result.stdout
    assert "=== Installing System Dependencies ===" in result.stdout
    assert "=== Installing DeepFilterNet ===" in result.stdout
    assert "=== Installing whisper.cpp ===" in result.stdout
    assert "✅ All tools installed successfully!" in result.stdout
