import platform
import subprocess
import sys

from waddle.tools.install_deep_filter import install_deep_filter
from waddle.tools.install_whisper_cpp import install_whisper_cpp


def check_dependency_installed(command):
    """Check if a command is available in the system PATH."""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_brew_package_installed(package):
    """Check if a Homebrew package is installed."""
    try:
        _ = subprocess.run(["brew", "list", package], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def install_system_dependencies():
    """Install system dependencies based on the current platform."""
    system = platform.system().lower()

    if system == "darwin":  # macOS
        print("Checking system dependencies...")

        # Check if Homebrew is installed
        if not check_dependency_installed("brew"):
            print("❌ Homebrew not found. Please install Homebrew first:")
            print("Visit https://brew.sh/ for installation instructions")
            return

        dependencies = [("ffmpeg", "ffmpeg"), ("cmake", "cmake"), ("fmt", "fmt")]

        for command, package in dependencies:
            if check_dependency_installed(command) or check_brew_package_installed(package):
                print(f"✅ {package} is already installed")
            else:
                try:
                    print(f"Installing {package}...")
                    subprocess.run(["brew", "install", package], check=True)
                    print(f"✅ {package} installed successfully")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to install {package}: {e}")
                    raise

    elif system == "linux":
        print("Checking system dependencies...")

        # Check individual dependencies
        dependencies = [
            ("ffmpeg", "ffmpeg"),
            ("cmake", "cmake"),
            ("pkg-config --exists fmt", "libfmt-dev"),
        ]

        packages_to_install = []
        for check_cmd, package in dependencies:
            try:
                subprocess.run(check_cmd.split(), capture_output=True, check=True)
                print(f"✅ {package} is already installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                packages_to_install.append(package)

        if packages_to_install:
            try:
                print("Updating package lists...")
                subprocess.run(["sudo", "apt", "update"], check=True)

                for package in packages_to_install:
                    print(f"Installing {package}...")
                    subprocess.run(["sudo", "apt", "install", "-y", package], check=True)
                    print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install system dependencies: {e}")
                raise
        else:
            print("✅ All system dependencies are already installed")

    else:
        print(f"⚠️  Automatic installation not supported for {system}")
        print("Please install the following dependencies manually:")
        print("- FFmpeg")
        print("- CMake")
        print("- fmt library")
        if system == "windows":
            print("\nFor Windows:")
            print("- Download FFmpeg from https://ffmpeg.org/download.html")
            print("- Install CMake from https://cmake.org/download/")
            print("- Install fmt library or use vcpkg")


def install_all_tools():
    """Install all necessary tools for waddle."""
    print("Installing all required tools for waddle...")

    try:
        # Install system dependencies first
        print("\n=== Installing System Dependencies ===")
        install_system_dependencies()

        # Install DeepFilterNet binary
        print("\n=== Installing DeepFilterNet ===")
        install_deep_filter()

        # Install whisper.cpp
        print("\n=== Installing whisper.cpp ===")
        install_whisper_cpp()

        print("\n✅ All tools installed successfully!")

    except Exception as e:
        print(f"\n❌ Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    install_all_tools()
