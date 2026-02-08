import cv2
import numpy as np
import mss
import pygetwindow as gw
import pyautogui
import time
import os
import subprocess
import ctypes

# Configuration
OUTPUT_FILENAME = "active_window_recording.mp4"
FPS = 15.0
CANVAS_SIZE = (1920, 1080)
PREVIEW_TITLE = "REC_PREVIEW"

# Windows API constants to minimize/hide windows
SW_MINIMIZE = 6
SW_HIDE = 0

def minimize_console():
    """Hides the console window so it's not captured."""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)

def main():
    # 1. Minimize the terminal immediately to get it out of the way
    minimize_console()

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(OUTPUT_FILENAME, fourcc, FPS, CANVAS_SIZE)

    print("--- Active Window Recorder Started ---")

    last_valid_target = None
    screen_w, screen_h = pyautogui.size()

    with mss.mss() as sct:
        try:
            while True:
                mouse_x, mouse_y = pyautogui.position()
                target_window = None

                try:
                    # Get all windows under the mouse
                    windows = gw.getWindowsAt(mouse_x, mouse_y)

                    for w in windows:
                        # Skip if window has no title or is the recorder's own preview
                        if not w.title.strip() or PREVIEW_TITLE in w.title:
                            continue

                        # Skip common system/recorder elements
                        title_lower = w.title.lower()
                        if any(x in title_lower for x in ["taskbar", "startrecorder", "powershell", "cmd.exe"]):
                            continue

                        target_window = w
                        break
                except:
                    pass

                # Sticky target: stay on last valid window if mouse is over empty space or recorder
                if target_window:
                    last_valid_target = target_window

                current_target = target_window or last_valid_target

                if current_target and current_target.width > 0 and current_target.height > 0:
                    try:
                        # Define the bounding box
                        monitor = {
                            "top": int(current_target.top),
                            "left": int(current_target.left),
                            "width": int(current_target.width),
                            "height": int(current_target.height)
                        }

                        # Capture pixels
                        img = np.array(sct.grab(monitor))
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                        # Create Canvas
                        canvas = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.uint8)

                        # Fit to 1080p
                        h, w = frame.shape[:2]
                        scale = min(CANVAS_SIZE[0]/w, CANVAS_SIZE[1]/h, 1.0)
                        if scale < 1.0:
                            frame = cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
                            h, w = frame.shape[:2]

                        canvas[0:h, 0:w] = frame

                        # Add a small text label at the bottom
                        cv2.putText(canvas, f"Recording: {current_target.title[:50]}", (10, CANVAS_SIZE[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

                        out.write(canvas)

                        # Show small preview in the corner
                        preview_frame = cv2.resize(canvas, (400, 225))
                        cv2.imshow(PREVIEW_TITLE, preview_frame)

                        # Move preview to bottom-right corner once it exists
                        # (Only needs to happen once or occasionally)
                        preview_hwnd = ctypes.windll.user32.FindWindowW(None, PREVIEW_TITLE)
                        if preview_hwnd:
                             ctypes.windll.user32.SetWindowPos(preview_hwnd, -1, screen_w - 420, screen_h - 300, 0, 0, 0x0001)

                    except:
                        pass

                # Press 'q' to stop
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                time.sleep(1/FPS)

        except KeyboardInterrupt:
            pass
        finally:
            out.release()
            cv2.destroyAllWindows()
            video_path = os.path.abspath(OUTPUT_FILENAME)
            # Re-show the folder
            subprocess.run(['explorer', '/select,', video_path])

if __name__ == "__main__":
    main()
