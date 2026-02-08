# Windows Smart Screen Recorder

A portable, zero-setup screen recording utility for Windows that can capture specific windows automatically based on your mouse cursor.

## 🚀 Quick Start

1. **Run the Script**: Double-click `StartRecorder.bat`.
2. **Automatic Setup**: The script will check for Python. If not found, it will automatically download and install it in the background.
3. **Recording**:
   - Hover your mouse over the window you want to record. The recorder will "lock" onto that window.
   - A small preview window will appear in the bottom-right of your screen.
   - **Note**: The recorder console and the preview window are automatically hidden from the actual video.
4. **Stop Recording**: Press the **'q'** key while the preview window is active.
5. **Find your Video**: Your recording will be saved to your **Downloads** folder and automatically highlighted in File Explorer.
6. **Cleanup**: The script will ask if you want to uninstall Python and the libraries to leave your PC clean.

## ✨ Features

- **Zero Configuration**: No need to manually install Python or libraries.
- **Smart Targetting**: Automatically captures the window under your mouse cursor.
- **Auto-Fallback**: If the target window is closed, it records the full screen for 5 seconds before pausing, giving you time to switch windows.
- **Privacy Focused**: Uses Windows API to exclude the recorder's own windows from being captured in the video.
- **Portable**: Can be run from any folder.

## 🛠️ Components

- `StartRecorder.bat`: The main entry point. Handles environment setup, installation, and cleanup.
- `recorder.py`: The core logic for window detection and video encoding.
- `requirements.txt`: List of necessary Python libraries (installed automatically).

## 📋 Requirements

- Windows 10 or 11.
- Internet connection (only for the first run to download Python/libraries).

---
**Tip**: If you already have Python installed, the script will detect it and skip the installation step!


---
**thanks for using**
-----