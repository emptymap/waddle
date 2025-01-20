#!/bin/bash

set -e  # Exit on any error

# Tool installation directories
TOOLS_DIR="./tools"
DEEP_FILTER_VERSION="0.5.6"
DEEP_FILTER_BASE_URL="https://github.com/Rikorose/DeepFilterNet/releases/download/v${DEEP_FILTER_VERSION}"

# Create the tools directory if it doesn't exist
mkdir -p "$TOOLS_DIR"

# Detect system architecture and platform
ARCH=$(uname -m)
OS=$(uname | tr '[:upper:]' '[:lower:]')

# Determine the correct binary for DeepFilterNet
case "$ARCH-$OS" in
  aarch64-darwin | arm64-darwin)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-aarch64-apple-darwin"
    ;;
  aarch64-linux | arm64-linux)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-aarch64-unknown-linux-gnu"
    ;;
  armv7l-linux | arm-linux)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-armv7-unknown-linux-gnueabihf"
    ;;
  x86_64-darwin)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-x86_64-apple-darwin"
    ;;
  x86_64-linux)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-x86_64-unknown-linux-musl"
    ;;
  x86_64-windows)
    DEEP_FILTER_BINARY="deep-filter-${DEEP_FILTER_VERSION}-x86_64-pc-windows-msvc.exe"
    ;;
  *)
    echo "Unsupported architecture or platform: $ARCH-$OS"
    exit 1
    ;;
esac

DEEP_FILTER_OUTPUT="$TOOLS_DIR/deep-filter"

# Download and install DeepFilterNet binary
if [ ! -f "$DEEP_FILTER_OUTPUT" ]; then
  echo "Downloading $DEEP_FILTER_BINARY..."
  if command -v curl &> /dev/null; then
    curl -L -o "$TOOLS_DIR/$DEEP_FILTER_BINARY" "$DEEP_FILTER_BASE_URL/$DEEP_FILTER_BINARY"
  elif command -v wget &> /dev/null; then
    wget -O "$TOOLS_DIR/$DEEP_FILTER_BINARY" "$DEEP_FILTER_BASE_URL/$DEEP_FILTER_BINARY"
  else
    echo "Error: curl or wget is required to download the binary."
    exit 1
  fi

  # Rename the binary to "deep-filter" and make it executable
  mv "$TOOLS_DIR/$DEEP_FILTER_BINARY" "$DEEP_FILTER_OUTPUT"
  chmod +x "$DEEP_FILTER_OUTPUT"
  echo "DeepFilterNet binary installed as: $DEEP_FILTER_OUTPUT"
else
  echo "DeepFilterNet binary already exists: $DEEP_FILTER_OUTPUT"
fi
