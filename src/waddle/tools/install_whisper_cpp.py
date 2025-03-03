import os
import subprocess
from pathlib import Path

from platformdirs import user_runtime_dir

from waddle.config import APP_AUTHOR, APP_NAME


def install_whisper_cpp():
    # Tool installation directories
    TOOLS_DIR = Path(user_runtime_dir(APP_NAME, APP_AUTHOR)) / "tools"
    WHISPER_DIR = TOOLS_DIR / "whisper.cpp"

    # Create the tools directory if it doesn't exist
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # Clone whisper.cpp if not already cloned
    if not WHISPER_DIR.is_dir():
        print("Cloning whisper.cpp repository...")
        subprocess.run(
            ["git", "clone", "https://github.com/ggerganov/whisper.cpp.git", str(WHISPER_DIR)],
            check=True,
        )
        subprocess.run(["git", "checkout", "v1.7.4"], check=True, cwd=str(WHISPER_DIR))
    else:
        print(f"whisper.cpp already exists at {WHISPER_DIR}")

    # Check if WHISPER_MODEL_NAME is defined, if not assign "large-v3" as default
    WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "large-v3")
    print(f"WHISPER_MODEL_NAME is set to: {WHISPER_MODEL_NAME}")

    # Download the model if not already downloaded
    model_path = WHISPER_DIR / "models" / f"ggml-{WHISPER_MODEL_NAME}.bin"
    if not model_path.is_file():
        print(f"Downloading the {WHISPER_MODEL_NAME} model...")
        subprocess.run(
            ["sh", "./models/download-ggml-model.sh", WHISPER_MODEL_NAME],
            check=True,
            cwd=WHISPER_DIR,
        )
    else:
        print(f"{WHISPER_MODEL_NAME} model already exists.")

    # Build the project
    print("Building whisper.cpp...")
    subprocess.run(["cmake", "-B", "build"], check=True, cwd=str(WHISPER_DIR))
    subprocess.run(
        ["cmake", "--build", "build", "--config", "Release"], check=True, cwd=str(WHISPER_DIR)
    )

    print(f"whisper.cpp installed successfully in: {WHISPER_DIR}")


if __name__ == "__main__":
    install_whisper_cpp()
