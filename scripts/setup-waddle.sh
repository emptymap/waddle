#!/bin/bash

set -e  # Exit on any error

sh ./scripts/install-all-tools.sh

echo "pip installing waddle..."
pip install -e .