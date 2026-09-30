from pathlib import Path
import subprocess
import sys
import time


ORDNER = Path(__file__).resolve().parent
AUTOSTART = ORDNER / "autostart.ps1"
BLOODY_SCAMMER = ORDNER / "we_got_you.py"
RUSSK_SCRIPT = ORDNER / "Russk.py"
RUSSK_DELAY_SECONDS = 17


def hidden_process_options() -> dict:
    if sys.platform != "win32":
        return {}

    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startup_info,
    }


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
        subprocess.Popen(
            ["py", "-3.11", str(BLOODY_SCAMMER)],
            cwd=ORDNER,
            start_new_session=True,
            **hidden_process_options(),
        )

    startzeit = time.monotonic()
    time.sleep(max(0, RUSSK_DELAY_SECONDS - (time.monotonic() - startzeit)))
    if RUSSK_SCRIPT.is_file():
        subprocess.Popen(
            [sys.executable, str(RUSSK_SCRIPT)],
            cwd=ORDNER,
            **hidden_process_options(),
        )


if __name__ == "__main__":
    starte()
