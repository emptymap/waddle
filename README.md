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

1. **Prepare Audio Files**:
   - Upload each speaker's audio files in the `audios` directory.
   - Use the naming convention: `ep{N}-{SpeakerName}.[wav|aifc|mp4]`.
     - Example: `ep1-Alice.wav`, `ep1-Bob.aifc`
   - Include a reference audio file that covers the entire podcast. The reference file name must start with `GMT` (e.g., a Zoom recording).

2. **Run Waddle**:
   Navigate to the `audios` directory and run:
   ```bash
   waddle
   ```

## Advanced Usage

Use the CLI to customize the processing:

```bash
waddle [options]
```

### Options:
- `-a`, `--audio`: Path to a single audio file to process. When provided, Waddle processes only this file in single-file mode.
- `-d`, `--directory`: Directory containing audio files (used in multi-file mode, default: `./`).
- `-r`, `--reference`: Path to the reference audio file (default: `None`).
- `-o`, `--output`: Path to save the output. For single-file mode, this is the directory for saving results. For multi-file mode, it is the synthesized audio file path.
- `-c`, `--comp_duration`: Duration (in seconds) for alignment comparison (default: `10`).
- `-od`, `--out_duration`: Duration (in seconds) for the output audio (default: `None`).
- `-nc`, `--no-convert`: Skip converting audio files to WAV format.

## Example Commands

### Podcast Preprocessing


1. **Basic Command**:
   Navigate to the folder containing your audio files and run:
   ```bash
   waddle
   ```

   This will process all audio files in the current directory, aligning, normalizing, and generating combined outputs.

2. **Specify a Directory**:
   Process audio files in a specific directory:
   ```bash
   waddle -d /path/to/audio/files
   ```

3. **Specify a Reference File**:
   Provide a custom reference audio file:
   ```bash
   waddle -r /path/to/GMT-Reference.wav
   ```

4. **Customize Output Duration**:
   Limit the output audio file duration to 30 seconds for testing:
   ```bash
   waddle -d /path/to/audio/files -od 30
   ```

5. **Skip Conversion**:
   If your audio files are already in WAV format:
   ```bash
   waddle -d /path/to/audio/files -nc
   ```

### Single-File Preprocessing

Process a single audio file:
```bash
waddle --audio path/to/audio.wav --output path/to/output/dir
```

This processes the specified file, normalizes it, detects speech segments, and generates an SRT file for subtitles.


## Output Files

### Podcast Preprocessing
- **Combined Audio**: A single audio file with all speakers combined.
- **Subtitle**: An SRT file with transcriptions for each speaker.
- **Each Speaker**: Individual audio files for each speaker with noise reduction.


### Single-File Preprocessing
- **Processed Audio**: The processed single audio file.
- **Subtitle**: An SRT file with transcription for the audio file.
