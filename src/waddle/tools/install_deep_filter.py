import os
import platform
import shutil
import sys
import urllib.request


def install_deep_filter():
    # Tool installation directories
    TOOLS_DIR = "./tools"
    DEEP_FILTER_VERSION = "0.5.6"
    DEEP_FILTER_BASE_URL = (
        f"https://github.com/Rikorose/DeepFilterNet/releases/download/v{DEEP_FILTER_VERSION}"
    )

    # Create the tools directory if it doesn't exist
    os.makedirs(TOOLS_DIR, exist_ok=True)

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
    DEEP_FILTER_OUTPUT = os.path.join(TOOLS_DIR, "deep-filter")

    # Download and install DeepFilterNet binary
    if not os.path.isfile(DEEP_FILTER_OUTPUT):
        print(f"Downloading {DEEP_FILTER_BINARY}...")
        download_url = f"{DEEP_FILTER_BASE_URL}/{DEEP_FILTER_BINARY}"
        binary_path = os.path.join(TOOLS_DIR, DEEP_FILTER_BINARY)

        try:
            urllib.request.urlretrieve(download_url, binary_path)
        except Exception as e:
            print(f"Error downloading file: {e}")
            sys.exit(1)

        # Rename the binary to "deep-filter" and make it executable
        shutil.move(binary_path, DEEP_FILTER_OUTPUT)
        os.chmod(DEEP_FILTER_OUTPUT, 0o755)
        print(f"DeepFilterNet binary installed as: {DEEP_FILTER_OUTPUT}")
    else:
        print(f"DeepFilterNet binary already exists: {DEEP_FILTER_OUTPUT}")


if __name__ == "__main__":
    install_deep_filter()
