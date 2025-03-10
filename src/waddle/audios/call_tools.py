import os
import subprocess
import tempfile
import threading
from pathlib import Path

from platformdirs import user_runtime_dir

from waddle.config import APP_AUTHOR, APP_NAME, DEFAULT_LANGUAGE
from waddle.tools.install_deep_filter import install_deep_filter
from waddle.tools.install_whisper_cpp import install_whisper_cpp


def get_tools_dir() -> Path:
    """
    Get the tools directory.
    """
    return Path(user_runtime_dir(APP_NAME, APP_AUTHOR)) / "tools"


def convert_to_mp3(
    input_path: Path, output_path_or_none: Path | None = None, force: bool = False
) -> None:
    """Convert audio file to MP3 format."""
    output_path = output_path_or_none or input_path.with_suffix(".mp3")
    if output_path.exists() and not force:
        print(f"[INFO] Skipping {input_path}: MP3 file already exists.")
        return

    # Convert to MP3 using ffmpeg
    print(f"[INFO] Converting {input_path} to {output_path}...")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(input_path),
                "-q:a",
                "0",
                str(output_path),
            ],
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
    if output_path.exists():
        print(f"[INFO] Skipping {input_path}: WAV file already exists.")
        return

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
        raise RuntimeError(f"[ERROR] Converting {input_path}: {e}") from e


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


def remove_noise(input_path: Path, output_path: Path) -> None:
    """
    Enhance audio by removing noise using DeepFilterNet.
    """
    # Paths
    tools_dir = get_tools_dir()
    deep_filter_path = tools_dir / "deep-filter"
    tmp_file_path = input_path.with_stem(input_path.stem + "_tmp")

    # Check if the tool exists
    with deep_filter_install_lock:
        if not deep_filter_path.exists():
            install_deep_filter()

    # Ensure input is 48kHz and 16-bit
    ensure_sampling_rate(input_path, tmp_file_path, target_rate=48000)

    # Run the DeepFilterNet tool without printing its output
    output_folder_path = output_path.parent
    command = [str(deep_filter_path), str(tmp_file_path), "-o", str(output_folder_path)]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        output_path.write_bytes(tmp_file_path.read_bytes())

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"[ERROR] Running DeepFilterNet: {e}") from e

    finally:
        # Cleanup temporary file
        if tmp_file_path.exists():
            tmp_file_path.unlink()


whisper_install_lock = threading.Lock()


def transcribe_in_batches(
    input_output_paths: list[tuple[Path, Path]],
    options: str = f"-l {DEFAULT_LANGUAGE}",
    *,
    batch_size: int = 200,
) -> None:
    """
    Transcribe audio in batches using Whisper.cpp.
    """

    # Paths
    tools_dir = get_tools_dir()
    whisper_bin = tools_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    whisper_model = (
        tools_dir
        / "whisper.cpp"
        / "models"
        / f"ggml-{os.getenv('WHISPER_MODEL_NAME') or 'large-v3'}.bin"
    )

    # Check if the Whisper binary exists
    with whisper_install_lock:
        if not whisper_model.exists():
            install_whisper_cpp()

    # Check if the Whisper model exists
    if not whisper_model.exists():
        raise FileNotFoundError(f"Whisper model not found. Please ensure {whisper_model} exists.")

    # List of pairs of tmp audio paths and output paths
    tmp_output_paths = []
    with tempfile.TemporaryDirectory() as temp_dir:
        for input_path, output_path in input_output_paths:
            # Ensure input is 16kHz and 16-bit
            tmp_audio_path = Path(temp_dir) / input_path.name
            ensure_sampling_rate(input_path, tmp_audio_path, target_rate=16000)
            tmp_output_paths.append((tmp_audio_path, output_path))

        batches = [
            tmp_output_paths[i : i + batch_size]
            for i in range(0, len(tmp_output_paths), batch_size)
        ]

        for batch in batches:
            command = [
                str(whisper_bin),
                "-m",
                str(whisper_model),
                *options.split(),
                "-osrt",
            ]
            for temp_audio_path, output_path in batch:
                command.extend([str(temp_audio_path), "-of", str(output_path)])
            try:
                subprocess.run(
                    command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                for _, output_path in batch:
                    Path(f"{output_path}.srt").replace(output_path)
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"[ERROR] Running Whisper: {e}") from e


def transcribe(
    input_path: Path, output_path: Path, options: str = f"-l {DEFAULT_LANGUAGE}"
) -> None:
    """
    Transcribe audio using Whisper.cpp.
    """
    # Paths
    tools_dir = get_tools_dir()
    whisper_bin = tools_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    whisper_model = (
        tools_dir
        / "whisper.cpp"
        / "models"
        / f"ggml-{os.getenv('WHISPER_MODEL_NAME') or 'large-v3'}.bin"
    )
    temp_audio_path = input_path.with_stem(input_path.stem + "_16k_16bit")

    # Check if the Whisper binary exists
    with whisper_install_lock:
        if not whisper_model.exists():
            install_whisper_cpp()

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
        str(temp_audio_path),
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
    finally:
        # Clean up the temporary file
        if temp_audio_path.exists():
            temp_audio_path.unlink()
