# USB-Stick-Ersteller Pro

Starte `usb_stick_ersteller.py` mit Python 3. Die Oberfläche unterstützt einen schnellen und stabilen Workflow:

1. Klicke auf **EXE auswählen...** und wähle die auszuführende Datei.
2. Wähle einen angeschlossenen USB-Stick aus und klicke auf **Stick erstellen**.
3. Klicke auf **Überwachung starten**. Wenn ein vorbereiteter Stick später eingesteckt wird, öffnet die App die konfigurierte Datei automatisch.
4. Auf einem neuen PC kannst du alternativ `START_USB.bat` auf dem Stick doppelt anklicken. Dafür muss Python dort nicht installiert sein.

Auf dem Stick werden die ausgewählte EXE, `START_USB.bat` und `usb_auto_start.json` gespeichert. Windows lässt einen Direktstart beim Einstecken aus Sicherheitsgründen nicht zu. Deshalb muss dieses Python-Programm auf dem Ziel-PC laufen, damit die vorbereitete Datei beim Einstecken wirklich gestartet wird.

Neu in der verbesserten Version:
- robustere USB-Erkennung und Aktualisierung
- klarere Statusausgabe mit Zeitstempel
- sichere Erstellung der Launcher-Dateien und Konfiguration
- verbesserte Validierung von Datei und Zielpfad
- einfacherer Zugriff auf den ausgewählten USB-Stick
- bessere Fehlerbehandlung bei fehlender oder ungültiger Konfiguration
- dunkles Design und System-Tray-Icon

## EXE und Installer bauen

Mit PowerShell im Projektordner:

```powershell
.\build_app.ps1
```

Danach liegen die Dateien hier:

- `dist\USB-Stick-Ersteller-Pro.exe`: portable Einzeldatei, Python ist auf dem Ziel-PC nicht nötig
- `USB-Stick-Ersteller-Pro-Setup.exe`: normaler Windows-Installer mit Startmenü- und Desktop-Verknüpfung

Der Installer bringt alle Python-Abhängigkeiten mit. Für einen neuen Build werden PyInstaller und Inno Setup benötigt; das Build-Skript findet Inno Setup automatisch in den üblichen Installationsordnern.