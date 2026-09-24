# Installiere (einmalig) das AudioDeviceCmdlets‑Modul
Install-Module -Name AudioDeviceCmdlets -Scope CurrentUser -Force
Import-Module AudioDeviceCmdlets

# Lautstärke um 10 % erhöhen (max. 100 %)
$step = 100
$current = (Get-AudioDevice -Playback).Volume
$new = [Math]::Min($current + $step, 100)

Set-AudioDevice -Playback -Volume $new

# Optional: Ausgabe der neuen Lautstärke
Write-Host "L"
