Building Camera Dashboard Binary
Quick Start

    Activate your virtual environment:

bash
source .venv/bin/activate

Make the build script executable:

bash
chmod +x build_binary.sh

Run the build:

bash
./build_binary.sh

Test the binary:

    bash
    ./dist/camera_dashboard

Manual Build (without script)
Install PyInstaller

bash
source .venv/bin/activate
pip install pyinstaller

Option 1: Using the spec file (recommended)

bash
pyinstaller --clean camera_dashboard.spec

Option 2: Direct command line

bash
pyinstaller \
 --onefile \
 --name camera_dashboard \
 --noconsole \
 --hidden-import PyQt6.QtCore \
 --hidden-import PyQt6.QtGui \
 --hidden-import PyQt6.QtWidgets \
 --hidden-import cv2 \
 --hidden-import pyudev \
 main.py

Build Flags Explained

    --onefile : Creates a single executable file

    --name camera_dashboard : Names the output binary

    --noconsole : Hides the console window (GUI only)

    --hidden-import : Forces inclusion of modules PyInstaller might miss

    --exclude-module : Removes unused large dependencies to reduce size

    --clean : Cleans PyInstaller cache before building

Important Notes
Build on Target Platform

Always build the binary ON the Raspberry Pi itself. PyInstaller does not support cross-compilation from x86 to ARM.
If you see "no pre-compiled bootloader" errors:

This is rare on current Pi OS with Python 3.9+, but if it happens:

bash
pip install --upgrade pyinstaller

# or build bootloader from source (advanced)

Console Mode vs No Console

    With console (--console or remove --noconsole): Shows log output in terminal

    Without console (--noconsole): Clean GUI, no terminal window

        Logs go to syslog or are lost; useful for production kiosk

For debugging, use --console mode during development
