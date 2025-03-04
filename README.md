# Waddle 🦆

**Waddle** is a preprocessor for podcasts, developed specifically for [RubberDuck.fm](https://rubberduck.fm). It streamlines the process of aligning, normalizing, and transcribing podcast audio files from multiple speakers or individual audio files.

![Demo](https://github.com/emptymap/waddle/blob/main/assets/demo.gif?raw=true)

## Features

- **Alignment**: Automatically synchronizes the audio files of each speaker to ensure they are perfectly aligned with the reference audio.
- **Normalization**: Ensures consistent audio quality by normalizing audio levels.
- **Remove Noise**: Cleans up audio by reducing background noise for clearer output using [`DeepFilterNet`](https://github.com/Rikorose/DeepFilterNet).
- **Subtitle Generation**: Generates SRT subtitle files for transcription using [`whisper.cpp`](https://github.com/ggerganov/whisper.cpp).

## Installation

### From PyPI (Recommended)

Install Waddle directly from PyPI:

```bash
pip install waddle-ai
```

### From Source

1. Clone the repository:
   ```bash
   git clone https://github.com/emptymap/waddle.git
   cd waddle
   ```

2. Install with pip:
   ```bash
   pip install .
   ```

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

## Usage

### Prepare Audio Files
   - Upload each speaker's audio files to your working directory.
   - Use the naming convention: `ep{N}-{SpeakerName}.[wav|aifc|m4a|mp4]`.
     - Example: `ep1-Alice.wav`, `ep1-Bob.aifc`
   - Include a reference audio file that covers the entire podcast. The reference file name must start with `GMT` (e.g., a Zoom recording).

### CLI Commands

#### Single Audio Processing

Process a single audio file:
```bash
waddle single path/to/audio.wav
```

Options:
- `-o, --output`: Directory to save the output (default: `./out`).
- `-ss`: Start time in seconds (default: `0.0`).
- `-t, --time`: Limit output duration (seconds).
- `-nnr, --no-noise-remove`: Skip noise removal.
- `-wo, --whisper-options`: Options for Whisper transcription (default: `-l ja`).

#### Preprocessing Multiple Audio Files

Process and align multiple audio files:
```bash
waddle preprocess
```

Options:
- `-d, --directory`: Directory containing audio files (default: `./`).
- `-o, --output`: Output directory (default: `./out`).
- `-ss`: Start time in seconds (default: `0.0`).
- `-t, --time`: Limit output duration (seconds).
- `-nnr, --no-noise-remove`: Skip noise removal.
- `-r, --reference`: Reference audio file for alignment.
- `-c, --comp-duration`: Duration for alignment comparison (default: `1200` seconds/20 minutes).
- `-nc, --no-convert`: Skip conversion to WAV format.

#### Postprocessing Audio Files

Process audio files after alignment (silence removal, merging, transcription):
```bash
waddle postprocess
```

Options:
- `-d, --directory`: Directory containing audio files (default: `./`).
- `-o, --output`: Output directory (default: `./out`).
- `-ss`: Start time in seconds (default: `0.0`).
- `-t, --time`: Limit output duration (seconds).
- `-wo, --whisper-options`: Options for Whisper transcription (default: `-l ja`).

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

6. **Start Processing from a Specific Time Point**:
   ```bash
   waddle preprocess -ss 120
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

3. **Custom Whisper Options**:
   ```bash
   waddle single /path/to/audio.wav -wo "-l en"
   ```

## Developer Guide

This section provides guidelines for developers contributing to **Waddle**.

### Setting Up the Development Environment

1. **Clone the Repository**
   ```bash
   git clone https://github.com/emptymap/waddle.git
   cd waddle
   ```

2. **Install `uv` (Recommended)**
   We use [`uv`](https://github.com/astral-sh/uv) as a fast package manager.
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install Development Dependencies**
   ```bash
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

### Linting and Type Checking

We use `ruff` for linting and formatting, and `pyright` for type checking.

- **Fix linting issues and format code:**
  ```bash
  uv run ruff check --fix
  uv run ruff format
  ```

- **Check for linting errors without fixing:**
  ```bash
  uv run ruff check
  ```

- **Run type checking:**
  ```bash
  uv run pyright
  ```

### Code Structure

The **Waddle** repository is organized as follows:

```
src/
└── waddle/
    ├── __main__.py            # CLI entry point
    ├── argparse.py            # Command-line argument parsing
    ├── config.py              # Configuration settings
    ├── processor.py           # Main processing pipeline
    ├── utils.py               # Utility functions
    ├── audios/                # Audio processing modules
    │   ├── align_offset.py    # Audio alignment functionality
    │   ├── call_tools.py      # External tool integration
    │   └── clip.py            # Audio clipping functionality
    ├── processing/            # Core audio processing
    │   ├── combine.py         # Combining audio segments
    │   └── segment.py         # Audio segmentation
    └── tools/                 # Installation tools
        ├── install_deep_filter.py
        └── install_whisper_cpp.py
```

### Contributing

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Write Code & Add Tests**
   - Ensure all functions are covered with tests in `tests/`.

3. **Run Tests & Formatting**
   ```bash
   uv run pytest
   uv run ruff check --fix
   uv run ruff format
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add my new feature"
   ```

5. **Push and Create a Pull Request**
   ```bash
   git push origin feature/my-new-feature
   ```
   - Open a PR on GitHub and request a review.

### CI/CD

- **GitHub Actions** will run:
  - `pytest` for tests
  - `ruff check` for linting
  - `pyright` for type checking
  - `ruff format` for formatting
  - Code coverage report generation

### Releasing

Waddle is available on PyPI as [waddle-ai](https://pypi.org/project/waddle-ai/).

To create a new release:

1. Update the version in `pyproject.toml`
2. Create and push a new tag with the version prefixed by 'v' (e.g., `v0.1.1`)
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
3. GitHub Actions will automatically:
   - Run all tests and checks
   - Build the package
   - Publish to PyPI

The current version is specified in `pyproject.toml`.