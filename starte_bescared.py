from pathlib import Path
import subprocess
import sys
import time


ORDNER = Path(__file__).resolve().parent
AUTOSTART = ORDNER / "autostart.ps1"
BLOODY_SCAMMER = ORDNER / "bloody-scammer.ps1"
NEW_SCRIPT = ORDNER / "new.py"
RUSSK_SCRIPT = ORDNER / "Russk.py"
NEW_DELAY_SECONDS = 5
RUSSK_DELAY_SECONDS = 15


def starte() -> None:
    if AUTOSTART.is_file():
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(AUTOSTART),
            ],
            check=True,
            cwd=ORDNER,
        )

    if BLOODY_SCAMMER.is_file():
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(BLOODY_SCAMMER),
                "-WindowCount",
                "9999",
            ],
            check=True,
            cwd=ORDNER,
        )

    startzeit = time.monotonic()
    time.sleep(max(0, NEW_DELAY_SECONDS - (time.monotonic() - startzeit)))
    if NEW_SCRIPT.is_file():
        subprocess.Popen([sys.executable, str(NEW_SCRIPT)], cwd=ORDNER)

    time.sleep(max(0, RUSSK_DELAY_SECONDS - (time.monotonic() - startzeit)))
    if RUSSK_SCRIPT.is_file():
        subprocess.Popen([sys.executable, str(RUSSK_SCRIPT)], cwd=ORDNER)


if __name__ == "__main__":
    starte()
