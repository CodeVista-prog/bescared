from pathlib import Path
import subprocess
import sys


ORDNER = Path(__file__).resolve().parent
AUTOSTART = ORDNER / "autostart.ps1"
BLOODY_SCAMMER = ORDNER / "we_got_you.py"
RUSSK_SCRIPT = ORDNER / "Russk.py"


def python_command(script: Path) -> list[str]:
    if getattr(sys, "frozen", False):
        return ["py", "-3.11", str(script)]
    return [sys.executable, str(script)]


def starte() -> None:
#     if AUTOSTART.is_file():
#         subprocess.run(
#             [
#                 "powershell.exe",
#                 "-NoProfile",
#                 "-ExecutionPolicy",
#                 "Bypass",
#                 "-File",
#                 str(AUTOSTART),
#             ],
#             check=True,
#             cwd=ORDNER,
#         )

    if BLOODY_SCAMMER.is_file():
        subprocess.run(
            ["py", "-3.11", str(BLOODY_SCAMMER)],
            cwd=ORDNER,
            check=True,
        )

    if RUSSK_SCRIPT.is_file():
        subprocess.Popen(
            python_command(RUSSK_SCRIPT),
            cwd=ORDNER,
        )


if __name__ == "__main__":
    starte()
