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

### **Prepare Audio Files**:
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
  - `-od, --out_duration`: Limit output duration (seconds).

- `preprocess` - Process multiple audio files:
  ```bash
  waddle preprocess -d ./audios -r ./reference.wav -o ./output
  ```
  - `-d, --directory`: Directory containing audio files (default: `./`).
  - `-r, --reference`: Reference audio file for alignment.
  - `-o, --output`: Output directory (default: `./out`).
  - `-od, --out_duration`: Limit output duration (seconds).
  - `-c, --comp_duration`: Duration for alignment comparison (default: `10` seconds).
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
   waddle preprocess -od 30
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
   waddle single /path/to/audio.wav -od 30
   ```
