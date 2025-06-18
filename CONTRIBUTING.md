# Contributing to Waddle

Thank you for your interest in contributing to **Waddle**! This guide will help you get started with development and contribution workflows.

## Development Installation

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

## Setting Up the Development Environment

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

## Running Tests

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

## Linting and Formatting

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

## Code Structure

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

### Key Files and Directories:

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

## Contributing Guidelines

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

## CI/CD

- **GitHub Actions** will run:
  - `pytest` for tests
  - `ruff check` for linting
  - `ruff format` for formatting
  - Code coverage report generation

Ensure your changes pass CI before merging!