import platform
import sys
import urllib.request
from pathlib import Path

from platformdirs import user_runtime_dir

from waddle.config import APP_AUTHOR, APP_NAME


def install_deep_filter():
    # Tool installation directories
    TOOLS_DIR = Path(user_runtime_dir(APP_NAME, APP_AUTHOR)) / "tools"
    DEEP_FILTER_OUTPUT = TOOLS_DIR / "deep-filter"
    if DEEP_FILTER_OUTPUT.exists():
        print(f"DeepFilterNet binary already exists: {DEEP_FILTER_OUTPUT}")
        return

    DEEP_FILTER_VERSION = "0.5.6"
    DEEP_FILTER_BASE_URL = (
        f"https://github.com/Rikorose/DeepFilterNet/releases/download/v{DEEP_FILTER_VERSION}"
    )

    # Create the tools directory if it doesn't exist
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    # Detect system architecture and platform
    ARCH = platform.machine().lower()
    OS = platform.system().lower()

    # Determine the correct binary for DeepFilterNet
    ARCH_OS_MAP = {
        ("aarch64", "darwin"): f"deep-filter-{DEEP_FILTER_VERSION}-aarch64-apple-darwin",
        ("arm64", "darwin"): f"deep-filter-{DEEP_FILTER_VERSION}-aarch64-apple-darwin",
        ("aarch64", "linux"): f"deep-filter-{DEEP_FILTER_VERSION}-aarch64-unknown-linux-gnu",
        ("arm64", "linux"): f"deep-filter-{DEEP_FILTER_VERSION}-aarch64-unknown-linux-gnu",
        ("armv7l", "linux"): f"deep-filter-{DEEP_FILTER_VERSION}-armv7-unknown-linux-gnueabihf",
        ("arm", "linux"): f"deep-filter-{DEEP_FILTER_VERSION}-armv7-unknown-linux-gnueabihf",
        ("x86_64", "darwin"): f"deep-filter-{DEEP_FILTER_VERSION}-x86_64-apple-darwin",
        ("x86_64", "linux"): f"deep-filter-{DEEP_FILTER_VERSION}-x86_64-unknown-linux-musl",
        ("x86_64", "windows"): f"deep-filter-{DEEP_FILTER_VERSION}-x86_64-pc-windows-msvc.exe",
    }

    key = (ARCH, OS)
    if key not in ARCH_OS_MAP:
        print(f"Unsupported architecture or platform: {ARCH}-{OS}")
        sys.exit(1)

    DEEP_FILTER_BINARY = ARCH_OS_MAP[key]
    print(f"Downloading {DEEP_FILTER_BINARY}...")

    download_url = f"{DEEP_FILTER_BASE_URL}/{DEEP_FILTER_BINARY}"
    binary_path = TOOLS_DIR / DEEP_FILTER_BINARY

    try:
        urllib.request.urlretrieve(download_url, binary_path)
    except Exception as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

    # Rename the binary to "deep-filter" and make it executable
    binary_path.rename(DEEP_FILTER_OUTPUT)
    DEEP_FILTER_OUTPUT.chmod(0o755)
    print(f"DeepFilterNet binary installed as: {DEEP_FILTER_OUTPUT}")


if __name__ == "__main__":
    install_deep_filter()
