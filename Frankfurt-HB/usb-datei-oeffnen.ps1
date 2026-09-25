[Setup]
AppName=USB-Stick-Ersteller Pro
AppVersion=1.0.0
DefaultDirName={autopf}\USB-Stick-Ersteller Pro
DefaultGroupName=USB-Stick-Ersteller Pro
OutputBaseFilename=USB-Stick-Ersteller-Pro-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\USB-Stick-Ersteller-Pro.exe
CreateAppDir=yes
OutputDir=.

[Files]
Source: "dist\USB-Stick-Ersteller-Pro.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\USB-Stick-Ersteller Pro"; Filename: "{app}\USB-Stick-Ersteller-Pro.exe"
Name: "{commondesktop}\USB-Stick-Ersteller Pro"; Filename: "{app}\USB-Stick-Ersteller-Pro.exe"

[Run]
Filename: "{app}\USB-Stick-Ersteller-Pro.exe"; Description: "USB-Stick-Ersteller Pro starten"; Flags: nowait postinstall skipifsilent
