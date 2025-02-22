import os
import subprocess
import threading
from pathlib import Path

from waddle.config import DEFAULT_LANGUAGE


def get_project_root() -> Path:
    """
    Get the project root directory.
    """
    return Path(__file__).parent.parent.parent.parent.resolve()


def should_convert_to_wav(input_path: Path, output_path: Path) -> bool:
    """Check if conversion to WAV is needed."""
    if output_path.exists():
        print(f"[INFO] Skipping {input_path}: WAV file already exists.")
        return False
    return True


def run_ffmpeg_conversion(input_path: Path, output_path: Path) -> None:
    """Run ffmpeg to convert audio file to WAV format."""
    print(f"[INFO] Converting {input_path} to {output_path}...")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path), str(output_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"[INFO] Successfully converted: {output_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[ERROR] Converting {input_path}: {e}") from e


def convert_to_wav(input_path: Path, output_path_or_none: Path | None = None) -> None:
    """Convert audio file to WAV format."""
    output_path = output_path_or_none or input_path.with_suffix(".wav")
    if should_convert_to_wav(input_path, output_path):
        run_ffmpeg_conversion(input_path, output_path)


def convert_all_files_to_wav(folder_path: Path) -> None:
    """Convert all audio files in the specified folder to WAV format."""
    # File extensions to look for
    valid_extensions = (".m4a", ".aifc", ".mp4")

    # Find all valid files in the current directory and subdirectories
    folder = Path(folder_path)
    for input_path in folder.rglob("*"):
        if input_path.suffix in valid_extensions:
            convert_to_wav(input_path)


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
        raise RuntimeError(f"[ERROR] Converting {input_path} to {output_path}: {e}") from e


deep_filter_install_lock = threading.Lock()


def ensure_deep_filter_installed() -> Path:
    """Ensure DeepFilterNet is installed and return its path."""
    project_root = get_project_root()
    deep_filter_path = project_root / "tools" / "deep-filter"

    with deep_filter_install_lock:
        if not deep_filter_path.exists():
            command = str(project_root / "scripts" / "install-deep-filter.sh")
            print("DeepFilterNet tool not found. Installing...")
            subprocess.run(command, check=True)

    return deep_filter_path


def run_deep_filter(input_path: Path, output_path: Path, tmp_file_path: Path) -> None:
    """Run DeepFilterNet noise removal."""
    output_folder_path = output_path.parent
    command = [
        str(ensure_deep_filter_installed()),
        str(tmp_file_path),
        "-o",
        str(output_folder_path),
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        output_path.write_bytes(tmp_file_path.read_bytes())
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[ERROR] Running DeepFilterNet: {e}") from e


def remove_noise(input_path: Path, output_path: Path) -> None:
    """Enhance audio by removing noise using DeepFilterNet."""
    tmp_file_path = input_path.with_stem(input_path.stem + "_tmp")

    try:
        # Prepare audio for DeepFilterNet
        ensure_sampling_rate(input_path, tmp_file_path, target_rate=48000)

        # Run noise removal
        run_deep_filter(input_path, output_path, tmp_file_path)

    finally:
        # Cleanup
        if tmp_file_path.exists():
            tmp_file_path.unlink()


whisper_install_lock = threading.Lock()


def ensure_whisper_installed() -> tuple[Path, Path]:
    """Ensure Whisper.cpp is installed and return binary and model paths."""
    project_root = get_project_root()
    whisper_bin = project_root / "tools" / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    whisper_model = (
        project_root
        / "tools"
        / "whisper.cpp"
        / "models"
        / f"ggml-{os.getenv('WHISPER_MODEL_NAME') or 'large-v3'}.bin"
    )

    with whisper_install_lock:
        if not whisper_model.exists():
            command = str(project_root / "scripts" / "install-whisper-cpp.sh")
            print("Whisper-cli binary not found. Installing...")
            subprocess.run(command, check=True)

    if not whisper_model.exists():
        raise FileNotFoundError(f"Whisper model not found. Please ensure {whisper_model} exists.")

    return whisper_bin, whisper_model


def run_whisper_transcription(
    whisper_bin: Path,
    whisper_model: Path,
    input_path: Path,
    output_path: Path,
    options: str,
) -> None:
    """Run Whisper.cpp transcription."""
    command = [
        str(whisper_bin),
        "-m",
        str(whisper_model),
        "-f",
        str(input_path),
        *options.split(),
        "-osrt",
        "-of",
        output_path,
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(f"{output_path}.srt").replace(output_path)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[ERROR] Running Whisper: {e}") from e


def transcribe(
    input_path: Path,
    output_path: Path,
    options: str = f"-l {DEFAULT_LANGUAGE}",
) -> None:
    """Transcribe audio using Whisper.cpp."""
    temp_audio_path = input_path.with_stem(input_path.stem + "_16k_16bit")

    try:
        # Prepare audio for Whisper
        ensure_sampling_rate(input_path, temp_audio_path, target_rate=16000)

        # Get Whisper paths and run transcription
        whisper_bin, whisper_model = ensure_whisper_installed()
        run_whisper_transcription(whisper_bin, whisper_model, temp_audio_path, output_path, options)

    finally:
        # Cleanup
        if temp_audio_path.exists():
            temp_audio_path.unlink()
