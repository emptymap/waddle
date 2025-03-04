# Waddle 🦆

**Waddle** (`waddle-ai`) is a preprocessor for podcasts, developed specifically for [RubberDuck.fm](https://rubberduck.fm). It streamlines the process of aligning, normalizing, and transcribing podcast audio files from multiple speakers or individual audio files.

![Demo](https://github.com/emptymap/waddle/blob/main/assets/demo.gif?raw=true)

## Features

- **Alignment**: Automatically synchronizes the audio files of each speaker to ensure they are perfectly aligned with the reference audio.
- **Normalization**: Ensures consistent audio quality by normalizing audio levels.
- **Remove Noise**: Cleans up audio by reducing background noise for clearer output using [`DeepFilterNet`](https://github.com/Rikorose/DeepFilterNet).
- **Subtitle Generation**: Generates SRT subtitle files for transcription using [`whisper.cpp`](https://github.com/ggerganov/whisper.cpp).

## Prerequisites

Before using **Waddle**, ensure the following requirements are installed:

1. **Python 3.12 or higher**:
    - Install Python from [python.org](https://www.python.org/).

2. **FFmpeg**:
   - **MacOS**:
     ```bash
     brew install ffmpeg
     ```
   - **Ubuntu/Debian**:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - **Windows**:
     - Download and install FFmpeg from [FFmpeg Downloads](https://ffmpeg.org/download.html).
     - Ensure FFmpeg is added to your system's PATH.

3. **fmt** (A C++ formatting library for compiling `whisper.cpp`):
   - **MacOS**:
     ```bash
     brew install fmt
     ```
   - For other platforms, follow installation instructions from [fmt GitHub repository](https://github.com/fmtlib/fmt).

## Installation

You can install Waddle directly from PyPI:

```bash
pip install waddle-ai
```

Or install from source:

1. Clone the repository:
   ```bash
   git clone https://github.com/emptymap/waddle.git
   cd waddle
   pip install -e .
   ```

## Usage

### Prepare Audio Files
   - Upload each speaker's audio files in the `audios` directory.
   - Use the naming convention: `ep{N}-{SpeakerName}.[wav|aifc|m4a|mp4]`.
     - Example: `ep1-Alice.wav`, `ep1-Bob.aifc`
   - Include a reference audio file that covers the entire podcast. The reference file name must start with `GMT` (e.g., a Zoom recording).

### CLI Options

- `single` - Process a single audio file:
  ```bash
  waddle single path/to/audio.wav -o ./output
  ```
  - `-o, --output`: Output directory (default: `./out`).
  - `-t, --time`: Limit output duration (seconds).

- `preprocess` - Process multiple audio files:
  ```bash
  waddle preprocess -d ./audios -r ./reference.wav -o ./output
  ```
  - `-d, --directory`: Directory containing audio files (default: `./`).
  - `-r, --reference`: Reference audio file for alignment.
  - `-o, --output`: Output directory (default: `./out`).
  - `-t, --time`: Limit output duration (seconds).
  - `-c, --comp-duration`: Duration for alignment comparison (default: `10` seconds).
  - `-nc, --no-convert`: Skip conversion to WAV format.

## Example Commands

### Podcast Preprocessing

1. **Basic Processing**:
   ```bash
   waddle preprocess
   ```

2. **Specify an Audio Directory**:
   ```bash
   waddle preprocess -d /path/to/audio/files
   ```

3. **Use a Custom Reference File**:
   ```bash
   waddle preprocess -r /path/to/GMT-Reference.wav
   ```

4. **Limit Output Duration**:
   ```bash
   waddle preprocess -t 30
   ```

5. **Skip WAV Conversion**:
   ```bash
   waddle preprocess -nc
   ```

### Single Audio File Processing

1. **Basic Processing**:
   ```bash
   waddle single /path/to/audio.wav
   ```

2. **Limit Output Duration**:
   ```bash
   waddle single /path/to/audio.wav -t 30
   ```

## Developer Guide

This section provides guidelines for developers contributing to **Waddle**. It includes setting up the development environment, running tests, and maintaining code quality.

### Setting Up the Development Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/emptymap/waddle.git
   cd waddle
   ```

2. **Install `uv` (Required)**
   We use [`uv`](https://github.com/astral-sh/uv) as our package manager.
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install Dependencies**
   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```

### Running Tests

We use `pytest` with coverage analysis to ensure code quality.

- **Run all tests with coverage reporting:**
  ```bash
  uv run pytest --cov=src --cov-report=html
  ```
  This will generate a coverage report in `htmlcov/`.

- **Run a specific test file:**
  ```bash
  uv run pytest tests/test_example.py
  ```

- **Run tests with verbose output:**
  ```bash
  uv run pytest -v
  ```

### Linting and Formatting

We use `ruff` for linting and formatting, and `pyright` for type checking.

- **Fix linting issues and format code:**
  ```bash
  uv run ruff check --fix
  uv run ruff format
  ```

- **Run type checking:**
  ```bash
  uv run pyright
  ```

### Code Structure

The **Waddle** repository is organized as follows:

```
waddle/
├── .github/
│   └── workflows/         # CI/CD workflows
│       └── ci.yml        # Main CI pipeline and PyPI publishing
├── src/
│   └── waddle/           # Main package source
│       ├── __main__.py   # CLI entry point
│       ├── argparse.py   # CLI argument parsing
│       ├── config.py     # Configuration management
│       ├── processor.py  # Core processing logic
│       ├── utils.py      # Utility functions
│       ├── audios/       # Audio processing modules
│       │   ├── align_offset.py  # Audio alignment
│       │   ├── call_tools.py    # External tool integration
│       │   └── clip.py          # Audio clipping
│       └── processing/   # Audio processing modules
│           ├── combine.py  # Audio combining
│           └── segment.py  # Audio segmentation
├── tests/                # Test suite
│   ├── integration_test.py
│   └── ep0/             # Test audio files
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

### Publishing to PyPI

Waddle uses GitHub Actions to automatically publish releases to PyPI. To publish a new version:

1. Update the version in `pyproject.toml`
2. Create and push a new tag with the same version:
   ```bash
   git tag v0.1.0  # Use the same version as in pyproject.toml
   git push origin v0.1.0
   ```
3. The CI workflow will automatically:
   - Run all tests and checks
   - Build the package
   - Publish to PyPI if all checks pass

The published package will be available at: https://pypi.org/project/waddle-ai/

### Contributing

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Write Code & Tests**
   - Add tests for new features in `tests/`
   - Ensure type hints are used appropriately

3. **Run Quality Checks**
   ```bash
   uv run ruff check --fix
   uv run ruff format
   uv run pyright
   uv run pytest
   ```

4. **Create a Pull Request**
   - Push your changes and open a PR on GitHub
   - Ensure all CI checks pass
   - Request a review from maintainers

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
