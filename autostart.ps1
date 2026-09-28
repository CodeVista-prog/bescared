param(
    [switch]$Remove
)

$startupPath = [Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
if ([string]::IsNullOrWhiteSpace($startupPath)) {
    throw 'Der Autostart-Ordner des aktuellen Benutzers wurde nicht gefunden.'
}

$helloScriptPath = Join-Path $PSScriptRoot '.\Russk.py'
$shortcutPath = Join-Path $startupPath 'Hallo.lnk'

if (-not (Test-Path -LiteralPath $helloScriptPath)) {
    throw "Das Hallo-Skript wurde nicht gefunden: $helloScriptPath"
}

if ($Remove) {
    if (Test-Path -LiteralPath $shortcutPath) {
        Remove-Item -LiteralPath $shortcutPath
        Write-Host 'Der Hallo-Autostart wurde entfernt.'
    }
    else {
        Write-Host 'Es wurde kein Hallo-Autostart gefunden.'
    }
    return
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $PSHOME 'powershell.exe'
$shortcut.Arguments = '-NoProfile -WindowStyle Hidden -File "' + $helloScriptPath + '"'
$shortcut.WorkingDirectory = $PSScriptRoot
$shortcut.Save()

Write-Host "hallo.ps1 startet ab jetzt bei der Anmeldung: $shortcutPath"