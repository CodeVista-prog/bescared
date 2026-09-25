import json
import tempfile
import unittest
from pathlib import Path

import usb_stick_ersteller as app


class UsbStickAppHelperTests(unittest.TestCase):
    def test_build_launcher_content(self):
        content = app.build_launcher_content("mein_app.exe")
        self.assertIn("@echo off", content)
        self.assertIn("start \"\" \"%~dp0\\mein_app.exe\"", content)

    def test_write_usb_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            drive = Path(temp_dir)
            app.write_usb_config(drive, "mein_app.exe")
            config_path = drive / app.CONFIG_NAME
            self.assertTrue(config_path.exists())
            data = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(data["datei"], "mein_app.exe")
            self.assertIn("created_at", data)


if __name__ == "__main__":
    unittest.main()
