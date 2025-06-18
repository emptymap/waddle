import os
import shutil
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


def test_integration_init():
    """Tests the init command for creating folder structure in current directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        test_args = ["init"]

        # Change to the temporary directory
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            result = run_waddle_command(test_args)
            assert result.returncode == 0, f"Command failed with error: {result.stderr}"

            # Check that all required folders were created
            expected_folders = ["0_raw", "1_pre", "2_edited", "3_post", "4_meta"]
            for folder in expected_folders:
                folder_path = tmpdir_path / folder
                assert folder_path.exists() and folder_path.is_dir(), (
                    f"Folder {folder} was not created"
                )

        finally:
            os.chdir(original_cwd)


def test_integration_init_with_project_name():
    """Tests the init command for creating folder structure with project name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        project_name = "Test Episode"
        test_args = ["init", project_name]

        # Change to the temporary directory
        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            result = run_waddle_command(test_args)
            assert result.returncode == 0, f"Command failed with error: {result.stderr}"

            # Check that project directory was created
            project_path = tmpdir_path / project_name
            assert project_path.exists() and project_path.is_dir(), (
                f"Project directory {project_name} was not created"
            )

            # Check that all required folders were created inside the project directory
            expected_folders = ["0_raw", "1_pre", "2_edited", "3_post", "4_meta"]
            for folder in expected_folders:
                folder_path = project_path / folder
                assert folder_path.exists() and folder_path.is_dir(), (
                    f"Folder {folder} was not created in project directory"
                )

        finally:
            os.chdir(original_cwd)


def test_integration_waddle_flow():
    """Tests the complete Waddle Flow: init -> preprocess -> postprocess -> metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        project_name = "test_project"

        original_cwd = Path.cwd()
        os.chdir(tmpdir)

        try:
            # Step 1: Initialize project
            result = run_waddle_command(["init", project_name])
            assert result.returncode == 0, f"Init failed: {result.stderr}"

            project_path = tmpdir_path / project_name
            assert project_path.exists(), "Project directory not created"

            # Check folders were created
            for folder in ["0_raw", "1_pre", "2_edited", "3_post", "4_meta"]:
                folder_path = project_path / folder
                assert folder_path.exists(), f"Folder {folder} not created"

            # Change to project directory
            os.chdir(project_path)

            # Step 2: Copy test files to 0_raw
            test_files_dir = dir / "ep0"
            for file in test_files_dir.glob("*.wav"):
                shutil.copy(file, "0_raw/")

            # Step 3: Run preprocess
            result = run_waddle_command(["preprocess", "-ss", "5", "-t", "5"])
            assert result.returncode == 0, f"Preprocess failed: {result.stderr}"

            # Check 1_pre has output files
            pre_files = list(Path("1_pre").glob("*.wav"))
            assert len(pre_files) > 0, "No files in 1_pre after preprocess"

            # Step 4: Copy files from 1_pre to 2_edited (simulating manual editing)
            for file in Path("1_pre").glob("*.wav"):
                shutil.copy(file, "2_edited/")

            # Step 5: Run postprocess
            result = run_waddle_command(["postprocess", "-ss", "2", "-t", "3"])
            assert result.returncode == 0, f"Postprocess failed: {result.stderr}"

            # Check 3_post has output files
            post_files = list(Path("3_post").glob("*.wav"))
            assert len(post_files) > 0, "No audio files in 3_post after postprocess"

            srt_files = list(Path("3_post").glob("*.srt"))
            assert len(srt_files) > 0, "No SRT files in 3_post after postprocess"

            # Step 6: Run metadata (should find SRT automatically)
            result = run_waddle_command(["metadata"])
            assert result.returncode == 0, f"Metadata failed: {result.stderr}"

            # Check 4_meta has output files
            meta_files = list(Path("4_meta").iterdir())
            assert len(meta_files) > 0, "No files in 4_meta after metadata generation"

        finally:
            os.chdir(original_cwd)
