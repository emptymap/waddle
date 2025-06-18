# Waddle 🦆

**Waddle** is a preprocessor for podcasts, developed specifically for [RubberDuck.fm](https://rubberduck.fm). It streamlines the process of aligning, normalizing, and transcribing podcast audio files from multiple speakers or individual audio files.

![waddle](https://github.com/user-attachments/assets/40856b03-4d17-4a0c-abcc-93e5fefe1b19)


## Features

- **Alignment**: Automatically synchronizes the audio files of each speaker to ensure they are perfectly aligned with the reference audio.
- **Normalization**: Ensures consistent audio quality by normalizing audio levels.
- **Remove Noise**: Cleans up audio by reducing background noise for clearer output using [`DeepFilterNet`](https://github.com/Rikorose/DeepFilterNet).
- **Subtitle Generation**: Generates SRT subtitle files for transcription using [`whisper.cpp`](https://github.com/ggerganov/whisper.cpp).
- **Metadata Generation**: Processes annotated SRT files to create chapter markers and show notes for podcast episodes.


## Prerequisites

**Waddle** requires Python 3.13 or higher. All other dependencies can be installed automatically using the `waddle install` command.

## Installation

### Quick Start (Recommended)

1. Install waddle via pip:
   ```bash
   pip install waddle-ai
   ```

2. Install all required tools and dependencies:
   ```bash
   waddle install
   ```

3. You're ready to use **Waddle**!

### Manual Installation (Optional)

If you prefer to install dependencies manually:

1. **Python 3.13 or higher**:
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

3. **Dependencies for compiling `whisper.cpp`**:
   - **CMake**:
     - **MacOS**:
       ```bash
       brew install cmake
       ```
     - **Ubuntu/Debian**:
       ```bash
       sudo apt update
       sudo apt install cmake
       ```
   
   - **fmt**:
     - **MacOS**:
       ```bash
       brew install fmt
       ```
     - **Ubuntu/Debian**:
       ```bash
       sudo apt update
       sudo apt install libfmt-dev
       ```

### Development Installation
For developers who want to contribute to **Waddle**, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/emptymap/waddle.git
   cd waddle
   ```

2. Install Python dependencies and external tools:
    ```bash
    uv sync
    ```

3. Install additional tools:
    ```bash
    uv run waddle install
    ```

4. Ready to use **Waddle**!

## Waddle Flow

**Waddle Flow** is the recommended workflow for podcast production using Waddle. It follows a structured approach through five stages, each with its own directory:

### Initialize Project
First, create a new project with the 5-stage folder structure:
```bash
waddle init EPISODE_NUM
cd EPISODE_NUM
```
This creates the following directories:
- `0_raw/` - Raw audio files
- `1_pre/` - Preprocessed audio files  
- `2_edited/` - Manually edited audio files
- `3_post/` - Post-processed audio files
- `4_meta/` - Metadata files

### Stage 0: Raw (`0_raw/`)
Place your original audio recordings here:
- Upload each speaker's audio files using the naming convention: `ep{N}-{SpeakerName}.[wav|aifc|m4a|mp4]`
  - Example: `ep1-Alice.wav`, `ep1-Bob.aifc`
- Include a reference audio file that covers the entire podcast. The reference file name must start with `GMT` (e.g., a Zoom recording)
  - Example: `GMT-recording.wav`

### Stage 1: Preprocessed (`1_pre/`)
Use the `preprocess` command to align and clean audio files:
```bash
waddle preprocess
```
This stage produces aligned and cleaned audio files.

### Stage 2: Edited (`2_edited/`)
Manual editing stage for fine-tuning:
- Edit files from `1_pre/` using your preferred audio editor
- Remove unwanted sections, adjust levels, add effects
  - If you want to edit with transcription, you can run `waddle preprocess -tr` to generate SRT files for each speaker.
- Save edited files here

### Stage 3: Post-processed (`3_post/`)
Use the `postprocess` command to finalize audio:
```bash
waddle postprocess
```
This stage produces:
- Final merged audio
- Transcription (SRT files)

### Stage 4: Metadata (`4_meta/`)
Edit the SRT files in `3_post/` to add chapter markers and show notes. Then, generate podcast metadata:
```bash
waddle metadata
```
This stage produces:
- Chapter markers
- Show notes
- MP3 with embedded metadata

Then you can upload the final audio and metadata to your podcast hosting platform.

### Complete Workflow Example
```bash
# Initialize project
waddle init my-podcast
cd my-podcast

# Place raw files in 0_raw/
cp ~/recordings/* 0_raw/

# Stage 1: Preprocess
waddle preprocess

# Stage 2: Manual editing (use your audio editor such as Audacity)
# Edit files from 1_pre/ and save to 2_edited/

# Stage 3: Post-process  
waddle postprocess

# Edit 3_post/{episode_name}.srt to add chapter markers and show notes
# Example:
# 
# 1
# 00:00:00.000 --> 00:00:03.000
# alice: Welcome to our podcast!
#
# # Programming Discussion
#
# 2
# 00:00:03.000 --> 00:00:06.000
# bob: Today we'll discuss programming.
#
# - [Rust Language](https://rust-lang.org)

# Stage 4: Generate metadata
waddle metadata
```

## Commands

- `init` - Initialize a new waddle project with folder structure:
  ```bash
  waddle init [project_name]
  ```
  - `project_name` (optional): Name of the project directory. If not provided, creates folders in the current directory.
  - Creates the following folder structure:
    - `0_raw/` - Raw audio files
    - `1_pre/` - Preprocessed audio files
    - `2_edited/` - Manually edited audio files
    - `3_post/` - Post-processed audio files
    - `4_meta/` - Metadata files

- `install` - Install all required tools and dependencies:
  ```bash
  waddle install
  ```
  Automatically installs FFmpeg, CMake, fmt, DeepFilterNet, and whisper.cpp based on your platform (macOS/Linux).

- `single` - Process a single audio file:
  ```bash
  waddle single path/to/audio.wav -o ./output
  ```
  - `-o, --output`: Directory to save the output (default: `./out`).
  - `-ss`: Start time in seconds for the audio segment (default: 0.0).
  - `-t, --time`: Duration in seconds for the output audio (default: None).
  - `-wo, --whisper-options`: Options to pass to Whisper transcription (default: `-l ja`). You can change the default language by modifying src/config.py.
  - `-nnr, --no-noise-remove`: Skip removing noise from the audio. (no value required)

- `preprocess` - Process multiple audio files:
  ```bash
  waddle preprocess
  ```
  - `-d, --directory`: Directory containing audio files (default: `0_raw`).
  - `-o, --output`: Directory to save the output (default: `1_pre`).
  - `-ss`: Start time in seconds for the audio segment (default: 0.0).
  - `-t, --time`: Duration in seconds for the output audio (default: None).
  - `-wo, --whisper-options`: Options to pass to Whisper transcription (default: `-l ja`).
  - `-nnr, --no-noise-remove`: Skip removing noise from the audio. (no value required)
  - `-r, --reference`: Path to the reference audio file (used in multi-file mode).
  - `-c, --comp-duration`: Duration in seconds for alignment comparison (default: 1200.0s).
  - `-nc, --no-convert`: Skip converting audio files to WAV format. (no value required)
  - `-tr, --transcribe`: Transcribe the processed audio files. (no value required)

- `postprocess` - Process aligned audio files:
  ```bash
  waddle postprocess
  ```
  - `-d, --directory`: Directory containing audio files (default: `2_edited`).
  - `-o, --output`: Directory to save the output (default: `3_post`).
  - `-ss`: Start time in seconds for the audio segment (default: 0.0).
  - `-t, --time`: Duration in seconds for the output audio (default: None).
  - `-wo, --whisper-options`: Options to pass to Whisper transcription (default: `-l ja`).

- `metadata` - Generate metadata from an annotated SRT file:
  ```bash
  waddle metadata
  ```
  - `source` (optional): Path to the annotated SRT file (default: looks for SRT files in `3_post/`).
  - `-i, --input`: Path to the input audio file. If not specified, it will look for an audio file with the same name.
  - `-o, --output`: Directory to save the metadata and audio files (default: `4_meta`).

## Annotated SRT Format

When using the `metadata` command, your SRT file should include annotations:

- `# Chapter` markers define chapters (up to 6 levels with #)
- Chapter starts at the next SRT timestamp and ends before the next chapter
- Any other text is considered show notes
- Empty lines are ignored
- Use `;` to add newlines in show notes (the `;` will be deleted)

### Example

```
# Introduction

1
00:00:00.000 --> 00:00:03.000
alice: Welcome to our podcast!

2
00:00:03.000 --> 00:00:06.000
bob: Today we'll discuss programming.

## Topic 1: Rust

3
00:00:06.000 --> 00:00:09.000
alice: Let's talk about Rust.

- [Rust Language](https://rust-lang.org)
;
Great for systems programming!

4
00:00:09.000 --> 00:00:12.000
bob: I love its memory safety.

# Conclusion

5
00:00:12.000 --> 00:00:15.000
alice: Thanks for listening!
```

### Output Files

The above example would generate these files:

1. **chapters.txt**:
```
- (00:00) Introduction
- (00:06) Topic 1: Rust
- (00:12) Conclusion
```

2. **show_notes.md**:
```markdown
- [Rust Language](https://rust-lang.org)

Great for systems programming!
```

3. The chapter markers would also be embedded in the MP3 metadata for podcast apps

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
├── pyproject.toml              # Project metadata, dependencies, and tool configurations
├── src/                        # Main library source code
│   └── waddle/         
│       ├── __main__.py         # CLI entry point for Waddle
│       ├── argparse.py         # Handles CLI arguments and command parsing
│       ├── config.py           # Configuration settings for processing
│       ├── processor.py        # Core processing logic for audio preprocessing
│       ├── utils.py            # Helper functions for audio handling
│       ├── metadata.py         # Metadata generation from annotated SRT files
│       ├── processing/  
│       │   ├── combine.py      # Merges multiple audio sources
│       │   └── segment.py      # Segments audio into chunks
│       ├── audios/
│       │   ├── align_offset.py # Synchronization logic for alignment
│       │   └── call_tools.py   # Interfaces with external audio tools
│       └── utils_test.py       # Unit tests for utilities
├── tests/                      # Unit and integration tests
│   ├── integration_test.py     # End-to-end integration tests
│   └── ep0/                    # Sample audio files for testing
└── README.md                   # Documentation for installation and usage
```

#### Key Files and Directories:

- **`src/waddle/__main__.py`**  
  - CLI entry point for running Waddle.
  
- **`src/waddle/processor.py`**  
  - Core logic for aligning, normalizing, and transcribing audio.

- **`src/waddle/metadata.py`**  
  - Handles metadata generation from annotated SRT files.

- **`src/waddle/processing/combine.py`**  
  - Merges multiple speaker audio files into a single track.

- **`src/waddle/processing/segment.py`**  
  - Splits long audio into manageable segments.

- **`src/waddle/audios/align_offset.py`**  
  - Handles audio synchronization using a reference track.

- **`tests/integration_test.py`**  
  - Runs integration tests to validate the preprocessing pipeline.


## Tool Installation Details

**Waddle** automatically installs required tools in your user runtime directory:

- **Location**: The tools are installed in the platform-specific user runtime directory:
  - **Linux**: `/run/user/{uid}/waddle/tools/`
  - **macOS**: `~/Library/Caches/TemporaryItems/waddle/tools/`
  - **Windows**: `C:\Users\<username>\AppData\Local\Temp\waddle\tools\`

- **Installed Tools**:
  - **whisper.cpp**: Installed in `<runtime_dir>/tools/whisper.cpp/`
  - **DeepFilterNet**: Installed as `<runtime_dir>/tools/deep-filter`

The installation scripts (`src/waddle/tools/install_whisper_cpp.py` and `src/waddle/tools/install_deep_filter.py`) automatically detect your system architecture and download the appropriate binaries.


### Contributing

1. **Create a Feature Branch**
   ```bash
   git checkout -b feat/my-new-feature
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
   git commit -m "feat: Add my new feature"
   ```

5. **Push and Create a Pull Request**
   ```bash
   git push origin feat/my-new-feature
   ```
   - Open a PR on GitHub and request a review.

### CI/CD

- **GitHub Actions** will run:
  - `pytest` for tests
  - `ruff check` for linting
  - `ruff format` for formatting
  - Code coverage report generation

Ensure your changes pass CI before merging!
