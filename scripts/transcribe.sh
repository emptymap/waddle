#!/bin/bash

set -e  # Exit on error

# Paths to tools and models
WHISPER_BIN="./tools/whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL="./tools/whisper.cpp/models/ggml-base.bin"

# Ensure the whisper-cli binary exists
if [ ! -f "$WHISPER_BIN" ]; then
  echo "Error: whisper-cli binary not found at $WHISPER_BIN"
  exit 1
fi

# Ensure the Whisper model exists
if [ ! -f "$WHISPER_MODEL" ]; then
  echo "Error: Whisper model not found at $WHISPER_MODEL"
  exit 1
fi

# Check input arguments
if [ $# -ne 1 ]; then
  echo "Usage: $0 <input_audio_file>"
  exit 1
fi

INPUT_FILE=$1
INPUT_DIR=$(dirname "$INPUT_FILE")  # Parent directory of the input file
BASE_NAME=$(basename "$INPUT_FILE" | sed 's/\.[^.]*$//')  # File name without extension
OUT_DIR="${INPUT_DIR}/out"  # Output directory relative to the input file
WAV_FILE="${OUT_DIR}/${BASE_NAME}.wav"
OUTPUT_FILE="${OUT_DIR}/${BASE_NAME}.srt"

# Create the output directory if it doesn't exist
mkdir -p "$OUT_DIR"

# Convert input file to 16-bit WAV if needed
echo "Converting $INPUT_FILE to 16-bit WAV format in $OUT_DIR..."
ffmpeg -i "$INPUT_FILE" -ar 16000 -ac 1 -c:a pcm_s16le "$WAV_FILE" -y

# Transcribe the WAV file using whisper-cli
echo "Transcribing $WAV_FILE with Whisper..."
$WHISPER_BIN -m "$WHISPER_MODEL" -f "$WAV_FILE" -l ja -osrt

echo "Transcription saved to: $OUTPUT_FILE"
