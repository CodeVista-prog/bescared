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


def _safe_drive_root(path: str | Path) -> Path:
    drive = Path(path)
    if drive.name == "":
        drive = drive.parent
    return drive.anchor and drive or drive.resolve()


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

    unique_drives = []
    seen = set()
    for drive in drives:
        key = str(drive).upper()
        if key not in seen:
            seen.add(key)
            unique_drives.append(drive)
    return unique_drives


def validate_source_file(path: str | Path) -> str:
    source_path = Path(path).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")
    if source_path.is_dir():
        raise ValueError(f"A directory is not a valid source file: {source_path}")
    return source_path.name


def prepare_usb_drive(target_drive: str | Path, source_file: str | Path, target_file_name: str | None = None) -> dict[str, Path]:
    drive_path = Path(target_drive).expanduser()
    source_path = Path(source_file).expanduser()

    if not drive_path.exists():
        raise FileNotFoundError(f"USB drive does not exist: {drive_path}")
    if not source_path.exists():
        raise FileNotFoundError(f"File not found: {source_path}")
    if drive_path.is_file():
        raise ValueError(f"USB target must be a directory: {drive_path}")

    target_name = target_file_name or validate_source_file(source_path)
    target_file = drive_path / target_name

    shutil.copy2(source_path, target_file)

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
        "target_file_name": target_name,
        "target_exe_name": target_name,
        "launcher_name": STARTER_BAT_NAME,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_file": str(source_path),
    }
    config_path = drive_path / CONFIG_FILE_NAME
    config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "target_file": target_file,
        "target_exe": target_file,
        "launcher": launcher_path,
        "config": config_path,
    }


def open_target_file(path: str | Path) -> None:
    file_path = Path(path)
    if not file_path.exists():
        return

    if os.name == "nt":
        try:
            os.startfile(str(file_path))
            return
        except (AttributeError, OSError):
            subprocess.Popen(["cmd", "/c", "start", "", str(file_path)], cwd=str(file_path.parent), close_fds=True)
            return

    subprocess.Popen(["xdg-open", str(file_path)], cwd=str(file_path.parent), close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def launch_prepared_usb(stick_path: str | Path) -> None:
    drive = Path(stick_path)
    config_path = drive / CONFIG_FILE_NAME
    if not config_path.exists():
        return

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return

    target_name = payload.get("target_file_name") or payload.get("target_exe_name")
    if not target_name:
        return

    target_file = drive / target_name
    if not target_file.exists():
        return

    if target_file.suffix.lower() == ".exe":
        subprocess.Popen([str(target_file)], cwd=str(drive), close_fds=True)
    else:
        open_target_file(target_file)


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
        self._monitor_seen: set[str] = set()

        main = ttk.Frame(root, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Datei auswählen:").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 8))
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

    def set_status(self, message: str, is_error: bool = False) -> None:
        self.status_text.set(message)
        if is_error:
            self.root.update_idletasks()

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
            try:
                validate_source_file(file_path)
            except Exception as exc:
                messagebox.showwarning("Ungültige Datei", str(exc))
                return
            self.selected_exe.set(file_path)
            self.set_status(f"Datei ausgewählt: {file_path}")

    def create_usb(self) -> None:
        source_exe = self.selected_exe.get().strip()
        if not source_exe:
            messagebox.showwarning("Fehlende Auswahl", "Bitte wählen Sie zuerst eine Datei aus.")
            return

        drive = self.selected_drive.get().strip()
        if not drive:
            messagebox.showwarning("Kein USB-Stick", "Bitte wählen Sie einen USB-Stick aus.")
            return

        try:
            validate_source_file(source_exe)
            prepared = prepare_usb_drive(drive, source_exe)
            self.set_status(
                f"USB-Stick vorbereitet: {prepared['launcher']} | {prepared['config']}"
            )
            messagebox.showinfo("Erfolgreich", f"Der USB-Stick wurde vorbereitet:\n{drive}")
        except Exception as exc:  # pragma: no cover - GUI error path
            messagebox.showerror("Fehler", str(exc))
            self.set_status(f"Fehler: {exc}", is_error=True)

    def start_monitoring(self) -> None:
        if self.monitoring:
            return

        self.monitoring = True
        self.stop_event.clear()
        self.set_status("Überwachung gestartet.")
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def stop_monitoring(self) -> None:
        self.monitoring = False
        self.stop_event.set()
        self.set_status("Überwachung gestoppt.")

    def _monitor_loop(self) -> None:
        while not self.stop_event.is_set():
            current_drives = {str(path).upper(): path for path in list_usb_drives()}
            for drive_key, drive in current_drives.items():
                if (drive / CONFIG_FILE_NAME).exists():
                    if drive_key not in self._monitor_seen:
                        self._monitor_seen.add(drive_key)
                        self.root.after(0, self._handle_detected_drive, drive)
                else:
                    self._monitor_seen.discard(drive_key)
            time.sleep(1)

    def _handle_detected_drive(self, drive: Path) -> None:
        try:
            launch_prepared_usb(drive)
            self.set_status(f"Vorbereiteter Stick erkannt: {drive}")
        except Exception as exc:  # pragma: no cover - GUI error path
            self.set_status(f"Fehler beim Start: {exc}", is_error=True)


def main() -> None:
    root = Tk()
    app = USBStickCreatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

