$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $projectRoot "dist\USB-Stick-Ersteller-Pro.exe"
$installDir = Join-Path $env:ProgramFiles "USB-Stick-Ersteller Pro"

if (-not (Test-Path $exePath)) {
    throw "Die EXE wurde noch nicht gebaut. Bitte zuerst build_app.ps1 ausführen."
}

New-Item -ItemType Directory -Path $installDir -Force | Out-Null
Copy-Item $exePath $installDir -Force

$shortcutDir = Join-Path $env:ProgramData "Microsoft\Windows\Start Menu\Programs\USB-Stick-Ersteller Pro"
New-Item -ItemType Directory -Path $shortcutDir -Force | Out-Null

$WScriptShell = New-Object -ComObject WScript.Shell
$shortcut = $WScriptShell.CreateShortcut((Join-Path $shortcutDir "USB-Stick-Ersteller Pro.lnk"))
$shortcut.TargetPath = Join-Path $installDir "USB-Stick-Ersteller-Pro.exe"
$shortcut.WorkingDirectory = $installDir
$shortcut.IconLocation = Join-Path $installDir "USB-Stick-Ersteller-Pro.exe"
$shortcut.Save()

Write-Host "Installiert in: $installDir"
Write-Host "Startmenü-Verknüpfung: $shortcutDir"
