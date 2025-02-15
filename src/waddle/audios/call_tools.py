import subprocess
import threading
from pathlib import Path


def get_project_root() -> Path:
    """
    Get the project root directory.
    """
    return Path(__file__).parent.parent.parent.parent.resolve()


def convert_to_wav(folder_path: Path) -> None:
    """
    Convert audio files in the specified folder to WAV format.
    Overwrites existing files without user input.

    Args:
        folder_path (str): Path to the folder containing audio files.
    """
    # File extensions to look for
    valid_extensions = (".m4a", ".aifc", ".mp4")

    # Find all valid files in the current directory and subdirectories
    folder = Path(folder_path)
    for input_path in folder.rglob("*"):
        if input_path.suffix in valid_extensions:
            output_path = input_path.with_suffix(".wav")
            if output_path.exists():
                print(f"[INFO] Skipping {input_path}: WAV file already exists.")
                continue

            # Convert to WAV using ffmpeg
            print(f"[INFO] Converting {input_path} to {output_path}...")
            try:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(input_path),
                        str(output_path),
                    ],  # Added '-y' flag
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                print(f"[INFO] Successfully converted: {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"[Error] Converting {input_path}: {e.stderr.decode()}")


def ensure_sampling_rate(
    input_path: Path, output_path: Path, target_rate: int, bit_depth: str = "16"
) -> None:
    """
    Ensure the input WAV file has the specified sampling rate and bit depth.
    Converts the input file if needed.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    command = [
        "ffmpeg",
        "-i",
        str(input_path),  # Input file
        "-ar",
        str(target_rate),  # Set target sample rate
        "-ac",
        "1",  # Ensure mono channel
        "-c:a",
        f"pcm_s{bit_depth}le",  # Set bit depth
        str(output_path),  # Output file
        "-y",  # Overwrite output file
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg failed with error: {e}")
        raise


deep_filter_install_lock = threading.Lock()


def remove_noise(input_path: Path, output_path: Path) -> None:
    """
    Enhance audio by removing noise using DeepFilterNet.
    """
    # Paths
    project_root = get_project_root()
    deep_filter_path = project_root / "tools" / "deep-filter"
    output_dir = output_path.parent
    tmp_file = input_path.name.replace(".wav", "_tmp.wav")
    tmp_file_path = output_dir / tmp_file

    # Check if the tool exists
    with deep_filter_install_lock:
        if not deep_filter_path.exists():
            command = str(project_root / "scripts" / "install-deep-filter.sh")
            print(
                f"DeepFilterNet tool not found. Run the following command to install it: {command}"
            )
            # Even if we run this command, it will not print output
            subprocess.run(command, check=True)

    # Ensure input is 48kHz and 16-bit
    ensure_sampling_rate(input_path, tmp_file_path, target_rate=48000)

    # Run the DeepFilterNet tool without printing its output
    command = [str(deep_filter_path), str(tmp_file_path), "-o", str(output_dir)]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(tmp_file_path).rename(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running DeepFilterNet: {e}")
        raise


whisper_install_lock = threading.Lock()


def transcribe(input_path: Path, output_path: Path, language: str = "ja") -> None:
    """
    Transcribe audio using Whisper.cpp.
    """
    # Paths
    project_root = get_project_root()
    whisper_bin = project_root / "tools" / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    whisper_model = project_root / "tools" / "whisper.cpp" / "models" / "ggml-large-v3.bin"
    input_path = Path(input_path)
    output_path = Path(output_path)
    temp_audio_path = input_path.stem + "_16k_16bit.wav"

    # Check if the Whisper binary exists
    with whisper_install_lock:
        if not whisper_bin.exists():
            command = str(project_root / "scripts" / "install-whisper-cpp.sh")
            print(
                f"Whisper-cli binary not found. Run the following command to install it: {command}"
            )
            subprocess.run(command, check=True)

    # Check if the Whisper model exists
    if not whisper_model.exists():
        raise FileNotFoundError(f"Whisper model not found. Please ensure {whisper_model} exists.")

    # Ensure input is 16kHz and 16-bit
    ensure_sampling_rate(input_path, temp_audio_path, target_rate=16000)

    # Transcribe using Whisper without printing its output
    command = [
        str(whisper_bin),
        "-m",
        str(whisper_model),
        "-f",
        temp_audio_path,
        "-l",
        language,
        "-osrt",
        "-of",
        output_path,
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(f"{output_path}.srt").replace(output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running Whisper-cli: {e}")
        raise
    finally:
        # Clean up the temporary file
        temp_path = Path(temp_audio_path)
        if temp_path.exists():
            temp_path.unlink()
