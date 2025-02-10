import os
import subprocess


def get_project_root() -> str:
    """
    Get the project root directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))


def convert_to_wav(folder_path: str) -> None:
    """
    Convert audio files in the specified folder to WAV format.
    Overwrites existing files without user input.

    Args:
        folder_path (str): Path to the folder containing audio files.
    """
    # File extensions to look for
    valid_extensions = (".m4a", ".aifc", ".mp4")

    # Find all valid files in the current directory and subdirectories
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(valid_extensions):
                input_path = os.path.join(root, file)
                output_path = os.path.splitext(input_path)[0] + ".wav"

                if os.path.exists(output_path):
                    print(f"Skipping {input_path}: WAV file already exists.")
                    continue

                # Convert to WAV using ffmpeg
                print(f"Converting {input_path} to {output_path}...")
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            input_path,
                            output_path,
                        ],  # Added '-y' flag
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    print(f"Successfully converted: {output_path}")
                except subprocess.CalledProcessError as e:
                    print(f"Error converting {input_path}: {e.stderr.decode()}")


def ensure_sampling_rate(
    input_path: str, output_path: str, target_rate: int, bit_depth: str = "16"
) -> None:
    """
    Ensure the input WAV file has the specified sampling rate and bit depth.
    Converts the input file if needed.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    command = [
        "ffmpeg",
        "-i",
        input_path,  # Input file
        "-ar",
        str(target_rate),  # Set target sample rate
        "-ac",
        "1",  # Ensure mono channel
        "-c:a",
        f"pcm_s{bit_depth}le",  # Set bit depth
        output_path,  # Output file
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


def remove_noise(input_path: str, output_path: str) -> None:
    """
    Enhance audio by removing noise using DeepFilterNet.
    """
    # Paths
    project_root = get_project_root()
    deep_filter_path = os.path.join(project_root, "tools/deep-filter")
    output_dir = os.path.dirname(output_path)
    tmp_file = os.path.basename(input_path).replace(".wav", "_tmp.wav")
    tmp_file_path = os.path.join(output_dir, tmp_file)

    # Check if the tool exists
    if not os.path.exists(deep_filter_path):
        command = os.path.join(project_root, "scripts/install-deep-filter.sh")
        print(f"DeepFilterNet tool not found. Run the following command to install it: {command}")
        # Even if we run this command, it will not print output
        subprocess.run(command, check=True)
        raise FileNotFoundError(f"DeepFilterNet tool not found: {deep_filter_path}")

    # Ensure input is 48kHz and 16-bit
    ensure_sampling_rate(input_path, tmp_file_path, target_rate=48000)

    # Run the DeepFilterNet tool without printing its output
    command = [deep_filter_path, tmp_file_path, "-o", output_dir]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.rename(tmp_file_path, output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running DeepFilterNet: {e}")
        raise


def transcribe(input_path: str, output_path: str, language: str = "ja") -> None:
    """
    Transcribe audio using Whisper.cpp.
    """
    # Paths
    project_root = get_project_root()
    whisper_bin = os.path.join(project_root, "tools/whisper.cpp/build/bin/whisper-cli")
    whisper_model = os.path.join(project_root, "tools/whisper.cpp/models/ggml-large-v3.bin")
    temp_audio_path = f"{os.path.splitext(input_path)[0]}_16k_16bit.wav"

    # Check if the Whisper binary exists
    if not os.path.exists(whisper_bin):
        command = os.path.join(project_root, "scripts/install-whisper-cpp.sh")
        print(f"Whisper-cli binary not found. Run the following command to install it: {command}")
        subprocess.run(command, check=True)
        raise FileNotFoundError(f"Whisper-cli binary not found: {whisper_bin}")

    # Check if the Whisper model exists
    if not os.path.exists(whisper_model):
        raise FileNotFoundError(f"Whisper model not found. Please ensure {whisper_model} exists.")

    # Ensure input is 16kHz and 16-bit
    ensure_sampling_rate(input_path, temp_audio_path, target_rate=16000)

    # Transcribe using Whisper without printing its output
    command = [
        whisper_bin,
        "-m",
        whisper_model,
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
        os.replace(f"{output_path}.srt", output_path)
    except subprocess.CalledProcessError as e:
        print(f"Error running Whisper-cli: {e}")
        raise
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
