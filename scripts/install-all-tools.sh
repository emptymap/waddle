#!/bin/bash

set -e  # Exit on any error

echo "Installing DeepFilterNet..."
sh ./scripts/install-deep-filter.sh

echo "Installing whisper.cpp..."
sh ./scripts/install-whisper-cpp.sh

echo "All tools installed successfully."
