from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from tkinter import StringVar, filedialog, messagebox, ttk
from tkinter import Tk


STARTER_BAT_NAME = "START_USB.bat"
CONFIG_FILE_NAME = "usb_auto_start.json"


def list_usb_drives() -> list[Path]:
    if os.name != "nt":
        return []

    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    system_drive = os.environ.get("SystemDrive", "C:")
    system_root = Path(f"{system_drive}\\")
    drives: list[Path] = []

    for index in range(26):
        if not (bitmask & (1 << index)):
            continue

        drive = Path(f"{chr(ord('A') + index)}:\\")
        try:
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(str(drive))
        except Exception:
            continue

        if drive == system_root:
            continue

        if drive_type in (2, 3, 4, 5):
            drives.append(drive)

    return drives


def prepare_usb_drive(target_drive: str | Path, source_exe: str | Path, target_exe_name: str | None = None) -> dict[str, Path]:
    drive_path = Path(target_drive)
    source_path = Path(source_exe)

    if not drive_path.exists():
        raise FileNotFoundError(f"USB drive does not exist: {drive_path}")
    if not source_path.exists():
        raise FileNotFoundError(f"Executable not found: {source_path}")

    target_name = target_exe_name or source_path.name
    target_exe = drive_path / target_name
    shutil.copy2(source_path, target_exe)

    launcher_path = drive_path / STARTER_BAT_NAME
    launcher_path.write_text(
        "@echo off\r\n"
        "setlocal\r\n"
        f'start "" "%~dp0{target_name}"\r\n'
        "exit /b 0\r\n",
        encoding="utf-8",
        newline="",
    )

    config = {
        "version": 1,
        "target_exe_name": target_name,
        "launcher_name": STARTER_BAT_NAME,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_exe": str(source_path),
    }
    config_path = drive_path / CONFIG_FILE_NAME
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "target_exe": target_exe,
        "launcher": launcher_path,
        "config": config_path,
    }


def launch_prepared_usb(stick_path: str | Path) -> None:
    drive = Path(stick_path)
    config_path = drive / CONFIG_FILE_NAME
    if not config_path.exists():
        return

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return

    target_name = payload.get("target_exe_name")
    if not target_name:
        return

    target_exe = drive / target_name
    if target_exe.exists():
        subprocess.Popen([str(target_exe)], cwd=str(drive), shell=True)


class USBStickCreatorApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("USB-Stick-Ersteller Pro")
        self.root.geometry("580x360")
        self.root.minsize(480, 280)

        self.selected_exe = StringVar(value="")
        self.selected_drive = StringVar(value="")
        self.status_text = StringVar(value="Bereit.")

        self.stop_event = threading.Event()
        self.monitoring = False

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="EXE auswählen:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        ttk.Entry(main, textvariable=self.selected_exe, width=52).grid(row=0, column=1, sticky="ew")
        ttk.Button(main, text="Durchsuchen", command=self.choose_exe).grid(row=0, column=2, padx=(8, 0))

        ttk.Label(main, text="USB-Stick:").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
        self.drive_combo = ttk.Combobox(main, textvariable=self.selected_drive, state="readonly", width=52)
        self.drive_combo.grid(row=1, column=1, sticky="ew")
        ttk.Button(main, text="Aktualisieren", command=self.refresh_drives).grid(row=1, column=2, padx=(8, 0))

        actions = ttk.Frame(main)
        actions.grid(row=2, column=0, columnspan=3, pady=(8, 10), sticky="ew")

        ttk.Button(actions, text="Stick erstellen", command=self.create_usb).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="Überwachung starten", command=self.start_monitoring).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="Überwachung stoppen", command=self.stop_monitoring).pack(side="left")

        ttk.Label(main, textvariable=self.status_text, foreground="#0a5f0a").grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        main.columnconfigure(1, weight=1)
        self.refresh_drives()

    def refresh_drives(self) -> None:
        drives = [str(path) for path in list_usb_drives()]
        self.drive_combo['values'] = drives
        if drives:
            if self.selected_drive.get() not in drives:
                self.selected_drive.set(drives[0])
        else:
            self.selected_drive.set("")

    def choose_exe(self) -> None:
        file_path = filedialog.askopenfilename(
            title="EXE wählen",
            filetypes=[("Ausführbare Dateien", "*.exe"), ("Alle Dateien", "*.*")],
        )
        if file_path:
            self.selected_exe.set(file_path)
            self.status_text.set(f"Datei ausgewählt: {file_path}")

    def create_usb(self) -> None:
        source_exe = self.selected_exe.get().strip()
        if not source_exe:
            messagebox.showwarning("Fehlende Auswahl", "Bitte wählen Sie zuerst eine EXE-Datei aus.")
            return

        drive = self.selected_drive.get().strip()
        if not drive:
            messagebox.showwarning("Kein USB-Stick", "Bitte wählen Sie einen USB-Stick aus.")
            return

        try:
            prepared = prepare_usb_drive(drive, source_exe)
            self.status_text.set(
                f"USB-Stick vorbereitet: {prepared['launcher']} | {prepared['config']}"
            )
            messagebox.showinfo("Erfolgreich", f"Der USB-Stick wurde vorbereitet:\n{drive}")
        except Exception as exc:  # pragma: no cover - GUI error path
            messagebox.showerror("Fehler", str(exc))
            self.status_text.set(f"Fehler: {exc}")

    def start_monitoring(self) -> None:
        if self.monitoring:
            return

        self.monitoring = True
        self.stop_event.clear()
        self.status_text.set("Überwachung gestartet.")
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def stop_monitoring(self) -> None:
        self.monitoring = False
        self.stop_event.set()
        self.status_text.set("Überwachung gestoppt.")

    def _monitor_loop(self) -> None:
        seen: set[str] = set()
        while not self.stop_event.is_set():
            for drive in list_usb_drives():
                drive_key = str(drive)
                if (drive / CONFIG_FILE_NAME).exists():
                    if drive_key not in seen:
                        seen.add(drive_key)
                        self.root.after(0, self._handle_detected_drive, drive)
                else:
                    seen.discard(drive_key)
            time.sleep(1)

    def _handle_detected_drive(self, drive: Path) -> None:
        try:
            launch_prepared_usb(drive)
            self.status_text.set(f"Vorbereiteter Stick erkannt: {drive}")
        except Exception as exc:  # pragma: no cover - GUI error path
            self.status_text.set(f"Fehler beim Start: {exc}")


def main() -> None:
    root = Tk()
    app = USBStickCreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

