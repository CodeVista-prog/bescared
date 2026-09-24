from pathlib import Path
import subprocess
import sys


ORDNER = Path(__file__).parent
ENTPACKER = ORDNER / "entpacke_zip.py"
BLOODY_SCAMMER = ORDNER / "bloody-scammer.ps1"


def starte() -> None:
    if not ENTPACKER.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {ENTPACKER}")
    if not BLOODY_SCAMMER.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {BLOODY_SCAMMER}")

    subprocess.run([sys.executable, str(ENTPACKER)], check=True)
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(BLOODY_SCAMMER),
            "-WindowCount",
            "1",
        ],
        check=True,
    )


if __name__ == "__main__":
    starte()
