#!/bin/bash
# Doraemon 2D Render - Git Workflow
# Run locally to generate and commit image

set -e

# Get current commit hash
COMMIT_HASH=$(git rev-parse --short HEAD)

echo "========================================"
echo "Doraemon 2D Render"
echo "Commit: $COMMIT_HASH"
echo "========================================"

# Run Blender
blender --background --python run_doraemon.py

# Commit generated image
PNG_FILE="doraemon_2d_${COMMIT_HASH}.png"

if [ -f "$PNG_FILE" ]; then
    git add "$PNG_FILE"
    git commit -m "chore: auto-generate doraemon image [skip ci]"
    echo "Committed $PNG_FILE"
else
    echo "Error: PNG file not found"
    exit 1
fi