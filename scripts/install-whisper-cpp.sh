#!/bin/bash

set -e  # Exit on any error

# Tool installation directories
TOOLS_DIR="./tools"
WHISPER_DIR="$TOOLS_DIR/whisper.cpp"

# Create the tools directory if it doesn't exist
mkdir -p "$TOOLS_DIR"

# Clone whisper.cpp if not already cloned
if [ ! -d "$WHISPER_DIR" ]; then
  echo "Cloning whisper.cpp repository..."
  git clone https://github.com/ggerganov/whisper.cpp.git "$WHISPER_DIR"
else
  echo "whisper.cpp already exists at $WHISPER_DIR"
fi

# Navigate into the whisper.cpp directory
cd "$WHISPER_DIR"

# Download the large-v3 model if not already downloaded
if [ ! -f "./models/ggml-large-v3.bin" ]; then
  echo "Downloading the large-v3 model..."
  sh ./models/download-ggml-model.sh large-v3
else
  echo "large-v3 model already exists."
fi

# Build the project
echo "Building whisper.cpp..."
cmake -B build
cmake --build build --config Release

cd -

echo "whisper.cpp installed successfully in: $WHISPER_DIR"
