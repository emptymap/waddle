# Waddle 🦆

**Waddle** is a preprocessor for podcasts, developed specifically for [RubberDuck.fm](https://rubberduck.fm). It streamlines the process of aligning, normalizing, and transcribing podcast audio files from multiple speakers or individual audio files.

![Demo](./assets/demo.gif)

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

4. **Other Dependencies**:
   - If you run `./scripts/setup-waddle.sh` as shown in the installation steps below, the required dependencies, [`DeepFilterNet`](https://github.com/Rikorose/DeepFilterNet) and [`whisper.cpp`](https://github.com/ggerganov/whisper.cpp), will be installed automatically.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/emptymap/waddle.git
   ```

2. Set up the environment:
   ```bash
   chmod +x ./scripts/setup-waddle.sh && ./scripts/setup-waddle.sh
   ```

3. You’re ready to use **Waddle**!

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

2. **Install `uv` (Recommended)**
   We use [`uv`](https://github.com/astral-sh/uv) as a fast package manager.
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
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

We use `ruff` for linting and formatting.

- **Fix linting issues and format code automatically:**
  ```bash
  uv run ruff check --fix | uv run ruff format
  ```

- **Check for linting errors without fixing:**
  ```bash
  uv run ruff check
  ```

- **Format code without running lint checks:**
  ```bash
  uv run ruff format
  ```


### Code Structure

The **Waddle** repository is organized as follows:

```
waddle/
├── pyproject.toml      # Project metadata, dependencies, and tool configurations
├── scripts/            # Helper scripts for setup and processing
│   ├── install-all-tools.sh   # Installs all required dependencies
│   ├── install-deep-filter.sh # Installs DeepFilterNet for noise reduction
│   ├── install-whisper-cpp.sh # Installs whisper.cpp for transcription
│   ├── setup-waddle.sh        # Sets up the environment for Waddle
│   └── transcribe.sh          # Helper script for transcribing audio
├── src/                # Main library source code
│   ├── waddle/         
│   │   ├── __main__.py  # CLI entry point for Waddle
│   │   ├── argparse.py  # Handles CLI arguments and command parsing
│   │   ├── config.py    # Configuration settings for processing
│   │   ├── processor.py # Core processing logic for audio preprocessing
│   │   ├── utils.py     # Helper functions for audio handling
│   │   ├── processing/  
│   │   │   ├── combine.py   # Merges multiple audio sources
│   │   │   ├── segment.py   # Segments audio into chunks
│   │   ├── audios/
│   │   │   ├── align_offset.py  # Synchronization logic for alignment
│   │   │   ├── call_tools.py    # Interfaces with external audio tools
│   │   ├── utils_test.py  # Unit tests for utilities
│   └── waddle.egg-info/   # Packaging metadata for distribution
├── tests/               # Unit and integration tests
│   ├── integration_test.py   # End-to-end integration tests
│   ├── ep0/             # Sample audio files for testing
│   │   ├── GMT20250119-015233_Recording_1280x720.wav  # Reference audio
│   │   ├── ep12-kotaro.wav  # Example speaker audio
│   │   ├── ep12-masa.wav    # Example speaker audio
│   │   ├── ep12-shun.wav    # Example speaker audio
└── README.md           # Documentation for installation and usage
```

#### Key Files and Directories:

- **`src/waddle/__main__.py`**  
  - CLI entry point for running Waddle.
  
- **`src/waddle/processor.py`**  
  - Core logic for aligning, normalizing, and transcribing audio.

- **`src/waddle/processing/combine.py`**  
  - Merges multiple speaker audio files into a single track.

- **`src/waddle/processing/segment.py`**  
  - Splits long audio into manageable segments.

- **`src/waddle/audios/align_offset.py`**  
  - Handles audio synchronization using a reference track.

- **`tests/integration_test.py`**  
  - Runs integration tests to validate the preprocessing pipeline.



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
  - `ruff format` for formatting
  - Code coverage report generation

Ensure your changes pass CI before merging!
