# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Waddle is a Python-based podcast preprocessing library that aligns, normalizes, and transcribes audio files from multiple speakers. It's designed specifically for podcast production workflows.

## Development Commands

### Package Management
- **Package manager**: Uses `uv` (fast Python package manager)
- **Install dependencies**: `uv sync`
- **Run with dependencies**: `uv run <command>`

### Testing
- **Run tests**: `uv run pytest`
- **Run all tests with coverage**: `uv run pytest --cov=src --cov-report=html`
- **Run specific test file**: `uv run pytest tests/test_example.py`
- **Run integration tests**: `uv run pytest tests/integration_test.py`
- **Run unit tests**: `uv run pytest src/waddle/*_test.py`

### Code Quality
- **Check and format code**: `uv run ruff check` (must run after writing code)
- **Format code**: `uv run ruff format` (must run after writing code)
- **Type checking**: `uv run pyright` (configured for Python 3.13, basic mode)

### Running the CLI
- **CLI entry point**: `uv run waddle` or `python -m waddle`
- **Available commands**: `single`, `preprocess`, `postprocess`, `metadata`

## Architecture Overview

### Core Processing Pipeline
1. **Audio Alignment**: Uses cross-correlation to sync speaker audio files against a reference track (typically GMT-prefixed Zoom recordings)
2. **Audio Processing**: Normalization, noise removal via DeepFilterNet, and format conversion
3. **Segmentation**: Splits long audio into manageable chunks for processing
4. **Transcription**: Uses whisper.cpp for speech-to-text with SRT output
5. **Metadata Generation**: Creates chapter markers and show notes from annotated SRT files

### Key Modules
- **`processor.py`**: Core processing orchestration for single/multi-file workflows
- **`audios/align_offset.py`**: Audio synchronization using cross-correlation algorithms
- **`audios/call_tools.py`**: External tool integration (FFmpeg, whisper.cpp, DeepFilterNet)
- **`processing/combine.py`**: Multi-speaker audio merging and timeline management
- **`processing/segment.py`**: Speech detection and audio chunking
- **`metadata.py`**: Chapter and show notes generation from annotated SRT files
- **`tools/`**: Automatic installation scripts for whisper.cpp and DeepFilterNet

### External Dependencies
- **Runtime tools**: whisper.cpp (transcription) and DeepFilterNet (noise removal) are auto-installed to platform-specific cache directories
- **Audio processing**: librosa, pydub, soundfile for audio manipulation
- **System requirements**: FFmpeg, Python 3.13+, CMake and fmt for whisper.cpp compilation

### Testing Structure
- **Unit tests**: Co-located with source files using `*_test.py` pattern
- **Integration tests**: In `tests/` directory, tests end-to-end CLI workflows
- **Test data**: Sample audio files in `tests/ep0/` for integration testing

### Configuration
- **Default settings**: `config.py` contains audio processing defaults (sample rate: 48kHz, target dB levels, etc.)
- **Language defaults**: Japanese (`ja`) for whisper transcription, configurable via CLI

### CLI Design
- **Four main commands**: `single` (one file), `preprocess` (alignment), `postprocess` (processing aligned files), `metadata` (chapter generation)
- **Automatic reference detection**: Files starting with "GMT" are used as reference tracks
- **Output organization**: Structured output directories with processed audio, SRT files, and metadata

## Development Rules

- **Write simple code**: Keep implementations straightforward and readable
- **Write with type annotations**: Always include type hints for function parameters and return values
- **After writing code**: Always run `uv run ruff check` and `uv run ruff format`
- **Testing**: Use `uv run pytest` to run tests
- **Component tests**: Create `{filename}_test.py` in the same directory as the source file
- **Integration tests**: Write in the `tests/` folder

## Development Notes

- Tests are co-located with source code using `*_test.py` naming convention
- Uses pathlib extensively for cross-platform file handling
- Audio processing leverages NumPy arrays for performance
- Error handling includes colored terminal output for warnings
- Supports concurrent processing for multiple audio files