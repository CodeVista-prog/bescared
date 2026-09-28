import importlib.util
import json
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("usb_stick_ersteller.py")


def load_module():
    spec = importlib.util.spec_from_file_location("usb_stick_ersteller", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_usb_drive_creates_launcher_and_config(tmp_path):
    module = load_module()

    app_path = tmp_path / "demo.txt"
    app_path.write_text("hello world", encoding="utf-8")

    drive = tmp_path / "usb_drive"
    drive.mkdir()

    prepared = module.prepare_usb_drive(drive, str(app_path), "demo.txt")

    assert prepared["launcher"] == drive / "START_USB.bat"
    assert prepared["config"] == drive / "usb_auto_start.json"
    assert (drive / "START_USB.bat").exists()
    assert (drive / "usb_auto_start.json").exists()

    payload = json.loads((drive / "usb_auto_start.json").read_text(encoding="utf-8"))
    assert payload["target_exe_name"] == "demo.txt"
    assert payload["launcher_name"] == "START_USB.bat"
