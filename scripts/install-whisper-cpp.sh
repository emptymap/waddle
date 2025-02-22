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

# Check if WHISPER_MODEL_NAME is defined, if not assign "large-v3" as default
if [ -z "$WHISPER_MODEL_NAME" ]; then
  WHISPER_MODEL_NAME="large-v3"
  echo "WHISPER_MODEL_NAME is not defined. Using default: $WHISPER_MODEL_NAME"
else
  echo "WHISPER_MODEL_NAME is set to: $WHISPER_MODEL_NAME"
fi

# Download the model if not already downloaded
if [ ! -f "./models/ggml-$WHISPER_MODEL_NAME.bin" ]; then
  echo "Downloading the $WHISPER_MODEL_NAME model..."
  sh ./models/download-ggml-model.sh $WHISPER_MODEL_NAME
else
  echo "$WHISPER_MODEL_NAME model already exists."
fi

# Build the project
echo "Building whisper.cpp..."
cmake -B build
cmake --build build --config Release

cd -

echo "whisper.cpp installed successfully in: $WHISPER_DIR"
