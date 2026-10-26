#!/usr/bin/env bash
# Builds a single-file Linux executable at dist/MathFighter
set -e
cd "$(dirname "$0")"
if ! python3 -c "import pygame, PyInstaller" 2>/dev/null; then
    echo "Setting up a virtual environment with pygame + PyInstaller..."
    python3 -m venv .venv
    . .venv/bin/activate
    pip install -r requirements.txt pyinstaller
fi
python3 -m PyInstaller --noconfirm --onefile --windowed --name MathFighter main.py
echo "Done: dist/MathFighter"
