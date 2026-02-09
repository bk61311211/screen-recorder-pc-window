import cv2
import numpy as np
import mss
import time
import os
import subprocess
import ctypes
from ctypes import wintypes
from datetime import datetime
import threading
import sounddevice as sd
import soundfile as sf
from imageio_ffmpeg import get_ffmpeg_exe
from pynput import keyboard

# --- Configuration ---
FPS = 20.0
FRAME_TIME = 1.0 / FPS
PREVIEW_TITLE = "REC_PREVIEW_WINDOW"
MIN_WINDOW_SIZE = 100
FALLBACK_DURATION = 5.0
SAMPLE_RATE = 44100
CHANNELS = 2

WDA_EXCLUDEFROMCAPTURE = 0x00000011

# --- Windows API Setup ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SCREEN_W = user32.GetSystemMetrics(0)
SCREEN_H = user32.GetSystemMetrics(1)
CANVAS_SIZE = (SCREEN_W, SCREEN_H)

GetCursorPos = user32.GetCursorPos
WindowFromPoint = user32.WindowFromPoint
GetAncestor = user32.GetAncestor
GetWindowRect = user32.GetWindowRect
IsWindowVisible = user32.IsWindowVisible
IsWindow = user32.IsWindow
FindWindowW = user32.FindWindowW
SetWindowPos = user32.SetWindowPos
GetConsoleWindow = kernel32.GetConsoleWindow
ShowWindow = user32.ShowWindow
SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity

def get_hwnd_at_mouse():
    try:
        pos = wintypes.POINT()
        GetCursorPos(ctypes.byref(pos))
        hwnd = WindowFromPoint(pos)
        return GetAncestor(hwnd, 2)
    except Exception:
        return None

class AudioRecorder:
    def __init__(self, filename):
        self.filename = filename
        self.recording = False
        self.paused = False
        self.audio_data = []
        self.stream = None

    def callback(self, indata, frames, time, status):
        if self.recording and not self.paused:
            self.audio_data.append(indata.copy())

    def start(self):
        self.recording = True
        device_id = None
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if "loopback" in dev['name'].lower() or "stereo mix" in dev['name'].lower():
                device_id = i
                break

        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                                     callback=self.callback, device=device_id)
        self.stream.start()

    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        if self.audio_data:
            all_audio = np.concatenate(self.audio_data, axis=0)
            sf.write(self.filename, all_audio, SAMPLE_RATE)

class GlobalController:
    def __init__(self):
        self.running = True
        self.paused = False
        self.listener = keyboard.GlobalHotKeys({
            '<ctrl>+q': self.on_quit,
            '<ctrl>+<enter>': self.on_pause
        })
        self.listener.start()

    def on_quit(self):
        print("\n[Global Hotkey] Ctrl+Q pressed. Stopping recording...")
        self.running = False

    def on_pause(self):
        self.paused = not self.paused
        print("\n[Global Hotkey] Ctrl+Enter pressed. Status: " + ("PAUSED" if self.paused else "RESUMED"))

def main():
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    temp_video = os.path.join(downloads_dir, f"temp_video_{timestamp}.mp4")
    temp_audio = os.path.join(downloads_dir, f"temp_audio_{timestamp}.wav")
    final_output = os.path.join(downloads_dir, f"ScreenRec_{timestamp}.mp4")

    console_hwnd = GetConsoleWindow()
    if console_hwnd:
        ShowWindow(console_hwnd, 6)
        SetWindowDisplayAffinity(console_hwnd, WDA_EXCLUDEFROMCAPTURE)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, FPS, CANVAS_SIZE)

    audio = AudioRecorder(temp_audio)
    audio.start()

    controller = GlobalController()

    print("--- Recorder Active ---")
    print("GLOBAL HOTKEYS:")
    print("  [Ctrl + Q]     : Stop Recording")
    print("  [Ctrl + Enter] : Pause / Resume")
    print(f"Resolution: {SCREEN_W}x{SCREEN_H}")

    active_target_hwnd = None
    fallback_start_time = 0

    with mss.mss() as sct:
        try:
            while controller.running:
                start_time = time.time()

                audio.paused = controller.paused

                potential_hwnd = get_hwnd_at_mouse()
                preview_hwnd = FindWindowW(None, PREVIEW_TITLE)

                is_valid_potential = False
                if potential_hwnd and IsWindowVisible(potential_hwnd):
                    if potential_hwnd not in [console_hwnd, preview_hwnd]:
                        rect = wintypes.RECT()
                        GetWindowRect(potential_hwnd, ctypes.byref(rect))
                        if (rect.right - rect.left) > MIN_WINDOW_SIZE and (rect.bottom - rect.top) > MIN_WINDOW_SIZE:
                            is_valid_potential = True

                if active_target_hwnd and not IsWindow(active_target_hwnd):
                    active_target_hwnd = None
                    fallback_start_time = time.time()

                if is_valid_potential:
                    active_target_hwnd = potential_hwnd
                    fallback_start_time = 0

                frame = None
                if not controller.paused:
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
                    elif time.time() - fallback_start_time < FALLBACK_DURATION:
                        img = np.array(sct.grab(sct.monitors[1]))
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                canvas = np.zeros((CANVAS_SIZE[1], CANVAS_SIZE[0], 3), dtype=np.uint8)
                if frame is not None:
                    fh, fw = frame.shape[:2]
                    scale = min(CANVAS_SIZE[0]/fw, CANVAS_SIZE[1]/fh, 1.0)
                    if scale < 1.0:
                        frame = cv2.resize(frame, (int(fw * scale), int(fh * scale)), interpolation=cv2.INTER_LANCZOS4)
                        fh, fw = frame.shape[:2]
                    y_offset = (CANVAS_SIZE[1] - fh) // 2
                    x_offset = (CANVAS_SIZE[0] - fw) // 2
                    canvas[y_offset:y_offset+fh, x_offset:x_offset+fw] = frame

                preview_h = 225
                preview_w = int(preview_h * (SCREEN_W / SCREEN_H))
                preview_img = cv2.resize(canvas, (preview_w, preview_h))

                if controller.paused:
                    cv2.rectangle(preview_img, (0,0), (preview_w, preview_h), (0,0,0), -1)
                    cv2.putText(preview_img, "PAUSED", (preview_w//4, preview_h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
                else:
                    cv2.circle(preview_img, (20, 20), 8, (0, 0, 255), -1)
                    cv2.putText(preview_img, "REC", (35, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

                if not controller.paused:
                    out.write(canvas)

                cv2.imshow(PREVIEW_TITLE, preview_img)

                if preview_hwnd:
                    SetWindowPos(preview_hwnd, -1, SCREEN_W - (preview_w + 20), SCREEN_H - (preview_h + 80), 0, 0, 0x0001)
                    SetWindowDisplayAffinity(preview_hwnd, WDA_EXCLUDEFROMCAPTURE)

                cv2.waitKey(1)

                elapsed = time.time() - start_time
                wait_time = FRAME_TIME - elapsed
                if wait_time > 0:
                    time.sleep(wait_time)

        finally:
            controller.listener.stop()
            out.release()
            audio.stop()
            cv2.destroyAllWindows()

            print("\nFinalizing video and audio (Merging)...")
            ffmpeg_exe = get_ffmpeg_exe()

            cmd = [
                ffmpeg_exe, "-y",
                "-i", temp_video,
                "-i", temp_audio,
                "-c:v", "copy",
                "-c:a", "aac",
                "-strict", "experimental",
                final_output
            ]

            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(temp_video): os.remove(temp_video)
            if os.path.exists(temp_audio): os.remove(temp_audio)

            print(f"Saved to: {final_output}")
            if os.path.exists(final_output):
                subprocess.run(['explorer', '/select,', final_output])

if __name__ == "__main__":
    main()
