import glob
import os
import subprocess
import sys
import tempfile
import wave

dir = os.path.dirname(os.path.abspath(__file__))


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
        input_file_path = os.path.join(dir, "ep0", input_file)

        test_args = ["single", input_file_path, "--output", tmpdir]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        output_file = os.path.join(tmpdir, input_file)
        assert os.path.exists(output_file), "Output file was not created"

        with wave.open(output_file, "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_single_file_not_found():
    """Tests handling of a missing input file by checking the expected FileNotFoundError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_file_path = os.path.join(dir, "ep0", "non_existent.wav")

        test_args = ["single", input_file_path, "--output", tmpdir]
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
        input_file_path = os.path.join(dir, "ep0", input_file)

        test_args = ["single", input_file_path, "--output", tmpdir, "-ss", "5", "-t", "5"]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        output_file = os.path.join(tmpdir, input_file.replace(".m4a", ".wav"))
        assert os.path.exists(output_file), "Output file was not created"

        with wave.open(output_file, "r") as wav_file:
            assert wav_file.getnchannels() > 0, "Invalid number of channels"
            assert wav_file.getsampwidth() > 0, "Invalid sample width"
            assert wav_file.getframerate() > 0, "Invalid frame rate"
            assert wav_file.getnframes() > 0, "No frames in output file"


def test_integration_preprocess():
    """Tests the preprocess command for batch processing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "preprocess",
            "--directory",
            os.path.join(dir, "ep0"),
            "--output",
            tmpdir,
            "-ss",
            "5",
            "-t",
            "5",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        wav_files = glob.glob(os.path.join(tmpdir, "*.wav"))
        assert len(wav_files) == 3, f"Expected 3 .wav files, but found {len(wav_files)}"

        lengths = [get_wav_duration(wav_file) for wav_file in wav_files]
        assert all(length == lengths[0] for length in lengths[1:]), (
            "Not all processed audio files have the same length"
        )

        reference_file = glob.glob(os.path.join(dir, "ep0", "GMT*"))[0]
        reference_length = get_wav_duration(reference_file)
        assert lengths[0] < reference_length, "Length of processed audio is not less than reference"


def test_integration_preprocess_no_reference():
    """Tests the preprocess command without a reference file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_args = [
            "preprocess",
            "--directory",
            os.path.join(dir, "ep0"),
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
        test_args = [
            "postprocess",
            "--directory",
            os.path.join(dir, "ep0"),
            "--output",
            tmpdir,
            "-ss",
            "10",
            "-t",
            "6",
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        wav_files = glob.glob(os.path.join(tmpdir, "*.wav"))
        assert len(wav_files) == 4, f"Expected 4 .wav files, but found {len(wav_files)}"
        assert get_wav_duration(wav_files[0]) < 6, "Output audio file has incorrect duration"

        srt_files = glob.glob(os.path.join(tmpdir, "*.srt"))
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
        test_args = [
            "metadata",
            os.path.join(dir, "ep0", "ep12.md"),
            "--input",
            os.path.join(dir, "ep0", "ep12-masa.wav"),
            "--output",
            tmpdir,
        ]
        result = run_waddle_command(test_args)

        assert result.returncode == 0, f"Command failed with error: {result.stderr}"

        files = os.listdir(tmpdir)
        print("Files in temporary directory:", files)

        mp3_file = os.path.join(tmpdir, "ep12-masa.mp3")
        assert os.path.exists(mp3_file), "MP3 file was not created"

        chapters_file = os.path.join(tmpdir, "ep12.chapters.txt")
        assert os.path.exists(chapters_file), "Chapters file was not created"

        show_notes_file = os.path.join(tmpdir, "ep12.show_notes.md")
        assert os.path.exists(show_notes_file), "Show notes file was not created"
