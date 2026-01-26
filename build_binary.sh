#!/usr/bin/env bash
# build_binary.sh - Build Camera Dashboard binary with PyInstaller

set -euo pipefail

echo "========================================"
echo "Camera Dashboard - PyInstaller Build"
echo "========================================"
echo

# Check if running in venv
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "WARNING: Not in a virtual environment!"
    echo "Activate your venv first: source .venv/bin/activate"
    exit 1
fi

# Check dependencies
if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Verify main.py exists
if [[ ! -f "main.py" ]]; then
    echo "ERROR: main.py not found in current directory!"
    exit 1
fi

echo "Building binary for Raspberry Pi / Linux ARM..."
echo

# Clean previous builds
if [[ -d "build" ]]; then
    echo "Cleaning old build directory..."
    rm -rf build
fi

if [[ -d "dist" ]]; then
    echo "Cleaning old dist directory..."
    rm -rf dist
fi

# Build with spec file if it exists, otherwise use command line
if [[ -f "camera_dashboard.spec" ]]; then
    echo "Using camera_dashboard.spec..."
    pyinstaller --clean camera_dashboard.spec
else
    echo "Building with default settings..."
    pyinstaller \
        --onefile \
        --name camera_dashboard \
        --noconsole \
        --hidden-import PyQt6.QtCore \
        --hidden-import PyQt6.QtGui \
        --hidden-import PyQt6.QtWidgets \
        --hidden-import cv2 \
        --hidden-import pyudev \
        --exclude-module matplotlib \
        --exclude-module tkinter \
        main.py
fi

echo
echo "========================================"
echo "Build complete!"
echo "========================================"
echo
echo "Binary location: ./dist/camera_dashboard"
echo
echo "To run:"
echo "  ./dist/camera_dashboard"
echo
echo "To install system-wide (optional):"
echo "  sudo cp dist/camera_dashboard /usr/local/bin/"
echo "  sudo chmod +x /usr/local/bin/camera_dashboard"
echo
