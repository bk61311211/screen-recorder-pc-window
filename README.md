# Windows Smart Screen Recorder

A portable, zero-setup screen recording utility for Windows that can capture specific windows automatically based on your mouse cursor.

## 🚀 Quick Start

1.  **Run the Script**: Double-click `StartRecorder.bat`.
2.  **Automatic Setup**: The script will check for Python and all required libraries. If not found, it will download and install them in the background.
3.  **Start Recording**: Once set up, the recorder will be active.
    *   Hover your mouse over any window to lock onto it.
    *   A preview window will appear in the bottom-right of your screen.
4.  **Control Recording**:
    *   **Pause/Resume**: Press **`Ctrl + Enter`** globally.
    *   **Stop Recording**: Press **`Ctrl + Q`** globally.
5.  **Find Your Video**: After stopping, the script will merge the video and audio. Your final recording will be saved in your **Downloads** folder and automatically selected in File Explorer.
6.  **Cleanup**: The script will ask if you want to uninstall Python and the libraries to leave your PC clean.

## ✨ Features

*   **Zero Configuration**: No need to manually install Python or libraries.
*   **Global Hotkeys**: Control the recorder from any application.
*   **Pause & Resume**: Start and stop the recording as needed.
*   **System Audio Capture**: Automatically records the sound playing from your speakers (Loopback/Stereo Mix).
*   **Smart Targetting**: Automatically captures the window under your mouse cursor.
*   **Native Resolution**: Records in your monitor's native resolution for the best quality.
*   **High-Quality Scaling**: Uses Lanczos interpolation to keep text and details sharp.
*   **Auto-Fallback**: If a target window closes, it records the full screen for 5 seconds.
*   **Privacy Focused**: Automatically hides the recorder's own windows from the final video.

## 🛠️ Components

*   `StartRecorder.bat`: The main entry point. Handles environment setup, installation, and cleanup.
*   `recorder.py`: The core logic for video/audio capture, window detection, and hotkeys.
*   `requirements.txt`: List of necessary Python libraries, installed automatically.

## 📋 Requirements

*   Windows 10 or 11.
*   Internet connection (only required for the first run if setup is needed).

---
*Thanks for using the Smart Screen Recorder!*