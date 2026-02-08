import cv2
import numpy as np
import mss
import time
import os
import subprocess
import ctypes
from ctypes import wintypes

# --- Configuration ---
OUTPUT_FILENAME = "active_window_recording.mp4"
FPS = 20.0  # Increased FPS for smoother capture
CANVAS_SIZE = (1920, 1080)
PREVIEW_TITLE = "REC_PREVIEW_WINDOW (Press 'q' to Stop)"
MIN_WINDOW_SIZE = 100 # Windows smaller than this (in pixels) will be ignored

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
    console_hwnd = GetConsoleWindow()
    if console_hwnd:
        ShowWindow(console_hwnd, 6) # SW_MINIMIZE

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, CANVAS_SIZE)

    print("--- Recorder Active ---")

    active_target_hwnd = None
    screen_w, screen_h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    with mss.mss() as sct:
        try:
            while True:
                # --- Target Acquisition Logic ---
                potential_hwnd = get_hwnd_at_mouse()
                preview_hwnd = FindWindowW(None, PREVIEW_TITLE)

                is_valid_target = False
                if potential_hwnd and IsWindowVisible(potential_hwnd):
                    # Exclude the recorder itself (console or preview)
                    if potential_hwnd not in [console_hwnd, preview_hwnd]:
                        rect = wintypes.RECT()
                        GetWindowRect(potential_hwnd, ctypes.byref(rect))
                        # Exclude tiny or invalid windows
                        if (rect.right - rect.left) > MIN_WINDOW_SIZE and (rect.bottom - rect.top) > MIN_WINDOW_SIZE:
                            is_valid_target = True

                if is_valid_target:
                    active_target_hwnd = potential_hwnd

                # --- Frame Capture Logic ---
                # Before capturing, do a "health check" on our locked target
                if active_target_hwnd and IsWindow(active_target_hwnd):
                    try:
                        rect = wintypes.RECT()
                        GetWindowRect(active_target_hwnd, ctypes.byref(rect))
                        monitor = {"top": rect.top, "left": rect.left, "width": rect.right - rect.left, "height": rect.bottom - rect.top}

                        img = np.array(sct.grab(monitor))
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                        canvas = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.uint8)
                        h, w = frame.shape[:2]

                        # Resize if window is larger than canvas
                        scale = min(CANVAS_SIZE[0]/w, CANVAS_SIZE[1]/h, 1.0)
                        if scale < 1.0:
                            frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                            h, w = frame.shape[:2]

                        # Calculate offsets to center the frame on the canvas
                        y_offset = (CANVAS_SIZE[1] - h) // 2
                        x_offset = (CANVAS_SIZE[0] - w) // 2

                        canvas[y_offset:y_offset+h, x_offset:x_offset+w] = frame
                        out.write(canvas)

                        # Display the final canvas in the preview
                        cv2.imshow(PREVIEW_TITLE, cv2.resize(canvas, (400, 225)))
                        if preview_hwnd:
                            SetWindowPos(preview_hwnd, -1, screen_w - 420, screen_h - 290, 0, 0, 0x0001)

                    except Exception as e:
                        # This can happen if a window closes abruptly. The health check will handle it.
                        active_target_hwnd = None
                else:
                    # If no valid target, show a "waiting" screen
                    canvas = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.uint8)
                    text = "Waiting for active window..."
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text_size = cv2.getTextSize(text, font, 1, 2)[0]
                    text_x = (CANVAS_SIZE[0] - text_size[0]) // 2
                    text_y = (CANVAS_SIZE[1] + text_size[1]) // 2
                    cv2.putText(canvas, text, (text_x, text_y), font, 1, (100, 100, 100), 2)
                    out.write(canvas)
                    cv2.imshow(PREVIEW_TITLE, cv2.resize(canvas, (400, 225)))

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            out.release()
            cv2.destroyAllWindows()
            video_path = os.path.abspath(OUTPUT_FILENAME)
            print(f"\nSaved: {video_path}")
            if os.path.exists(video_path):
                subprocess.run(['explorer', '/select,', video_path])

if __name__ == "__main__":
    main()
