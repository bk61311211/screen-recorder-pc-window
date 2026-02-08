import cv2
import numpy as np
import mss
import time
import os
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime

# --- Configuration ---
# This will now be generated dynamically in main()
FPS = 20.0  # Increased FPS for smoother capture
CANVAS_SIZE = (1920, 1080)
PREVIEW_TITLE = "REC_PREVIEW_WINDOW (Press 'q' to Stop)"
MIN_WINDOW_SIZE = 100 # Windows smaller than this (in pixels) will be ignored
FALLBACK_DURATION = 5.0 # Seconds to record full screen after window is closed

# Windows Display Affinity Constant (Available in Windows 10 2004+)
# 0x00000011: Excludes the window from being captured by screen recording.
WDA_EXCLUDEFROMCAPTURE = 0x00000011

# --- Windows API Setup ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Function pointers for more direct API calls
GetCursorPos = user32.GetCursorPos
WindowFromPoint = user32.WindowFromPoint
GetAncestor = user32.GetAncestor
GetWindowTextW = user32.GetWindowTextW
GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowRect = user32.GetWindowRect
IsWindowVisible = user32.IsWindowVisible
IsWindow = user32.IsWindow
FindWindowW = user32.FindWindowW
SetWindowPos = user32.SetWindowPos
GetConsoleWindow = kernel32.GetConsoleWindow
ShowWindow = user32.ShowWindow
SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity

def get_hwnd_at_mouse():
    """Gets the handle of the top-level window directly under the mouse."""
    try:
        pos = wintypes.POINT()
        GetCursorPos(ctypes.byref(pos))
        hwnd = WindowFromPoint(pos)
        return GetAncestor(hwnd, 2)  # GA_ROOT
    except Exception:
        return None

def get_window_title(hwnd):
    length = GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buff = ctypes.create_unicode_buffer(length + 1)
    GetWindowTextW(hwnd, buff, length + 1)
    return buff.value

def main():
    # Generate unique filename in Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(downloads_dir, f"ScreenRec_{timestamp}.mp4")

    console_hwnd = GetConsoleWindow()
    if console_hwnd:
        ShowWindow(console_hwnd, 6) # SW_MINIMIZE
        # Make the console invisible to capture
        SetWindowDisplayAffinity(console_hwnd, WDA_EXCLUDEFROMCAPTURE)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, FPS, CANVAS_SIZE)

    print("--- Recorder Active ---")
    print(f"Recording to: {output_path}")

    active_target_hwnd = None
    fallback_start_time = 0
    screen_w, screen_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    with mss.mss() as sct:
        try:
            while True:
                # --- Target Acquisition Logic ---
                potential_hwnd = get_hwnd_at_mouse()
                preview_hwnd = FindWindowW(None, PREVIEW_TITLE)

                is_valid_potential = False
                if potential_hwnd and IsWindowVisible(potential_hwnd):
                    # Exclude the recorder itself (console or preview)
                    if potential_hwnd not in [console_hwnd, preview_hwnd]:
                        rect = wintypes.RECT()
                        GetWindowRect(potential_hwnd, ctypes.byref(rect))
                        # Exclude tiny or invalid windows
                        if (rect.right - rect.left) > MIN_WINDOW_SIZE and (rect.bottom - rect.top) > MIN_WINDOW_SIZE:
                            is_valid_potential = True

                # If we were recording a window and it's now gone, start fallback
                if active_target_hwnd and not IsWindow(active_target_hwnd):
                    active_target_hwnd = None
                    fallback_start_time = time.time()
                    print("Target window closed. Starting 5s full-screen fallback.")

                # If we find a new valid window under the mouse, lock onto it
                if is_valid_potential:
                    active_target_hwnd = potential_hwnd
                    fallback_start_time = 0 # Cancel fallback if new window found

                # --- Frame Capture Logic ---
                frame = None

                # Case 1: Active Window
                if active_target_hwnd and IsWindow(active_target_hwnd):
                    try:
                        rect = wintypes.RECT()
                        GetWindowRect(active_target_hwnd, ctypes.byref(rect))
                        monitor = {"top": rect.top, "left": rect.left, "width": rect.right - rect.left, "height": rect.bottom - rect.top}
                        img = np.array(sct.grab(monitor))
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                    except:
                        active_target_hwnd = None
                        fallback_start_time = time.time()

                # Case 2: Fallback (Full Screen)
                elif time.time() - fallback_start_time < FALLBACK_DURATION:
                    # Capture primary monitor (sct.monitors[1])
                    img = np.array(sct.grab(sct.monitors[1]))
                    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                # --- Rendering Logic ---
                canvas = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.uint8)

                if frame is not None:
                    h, w = frame.shape[:2]
                    # Resize if window is larger than canvas
                    scale = min(CANVAS_SIZE[0]/w, CANVAS_SIZE[1]/h, 1.0)
                    if scale < 1.0:
                        frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                        h, w = frame.shape[:2]

                    # Centering
                    y_offset = (CANVAS_SIZE[1] - h) // 2
                    x_offset = (CANVAS_SIZE[0] - w) // 2
                    canvas[y_offset:y_offset+h, x_offset:x_offset+w] = frame
                else:
                    # Waiting screen
                    text = "Waiting for active window..."
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text_size = cv2.getTextSize(text, font, 1, 2)[0]
                    text_x = (CANVAS_SIZE[0] - text_size[0]) // 2
                    text_y = (CANVAS_SIZE[1] + text_size[1]) // 2
                    cv2.putText(canvas, text, (text_x, text_y), font, 1, (100, 100, 100), 2)

                out.write(canvas)
                cv2.imshow(PREVIEW_TITLE, cv2.resize(canvas, (400, 225)))

                # Apply transparency/exclusion to the preview window
                if preview_hwnd:
                    # Set position to bottom right
                    SetWindowPos(preview_hwnd, -1, screen_w - 420, screen_h - 290, 0, 0, 0x0001)
                    # Use Windows Display Affinity to make it invisible to capture software
                    SetWindowDisplayAffinity(preview_hwnd, WDA_EXCLUDEFROMCAPTURE)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            out.release()
            cv2.destroyAllWindows()
            print(f"\nSaved to: {output_path}")
            if os.path.exists(output_path):
                subprocess.run(['explorer', '/select,', output_path])

if __name__ == "__main__":
    main()
