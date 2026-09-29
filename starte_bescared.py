from pathlib import Path
import subprocess
import sys
import time


ORDNER = Path(__file__).parent
AUTOSTART = ORDNER / "autostart.ps1"
BLOODY_SCAMMER = ORDNER / "bloody-scammer.ps1"
NEW_SCRIPT = ORDNER / "new.py"
RUSSK_SCRIPT = ORDNER / "Russk.py"


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
        )

    time.sleep(5)
    if NEW_SCRIPT.is_file():
        subprocess.Popen([sys.executable, str(NEW_SCRIPT)])

    time.sleep(10)
    if RUSSK_SCRIPT.is_file():
        subprocess.Popen([sys.executable, str(RUSSK_SCRIPT)])


if __name__ == "__main__":
    starte()
