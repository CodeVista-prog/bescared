$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$distDir = Join-Path $projectRoot "dist"
$buildDir = Join-Path $projectRoot "build"
$appName = "USB-Stick-Ersteller-Pro"
$appFile = Join-Path $projectRoot "usb_stick_ersteller.py"

Write-Host "[1/3] Building EXE..."
& pyinstaller --noconfirm --onefile --windowed `
    --name $appName `
    --hidden-import pystray `
    --collect-all pystray `
    --hidden-import PIL `
    --collect-all PIL `
    --distpath $distDir `
    --workpath $buildDir `
    --specpath $projectRoot `
    $appFile

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Write-Host "[2/3] Locating Inno Setup..."
$isccCandidates = @(
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path $env:LOCALAPPDATA "Programs\Antigravity\resources\app\node_modules\innosetup\bin\ISCC.exe")
)
$isccPath = $isccCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $isccPath) {
    $isccCommand = Get-Command iscc -ErrorAction SilentlyContinue
    if ($isccCommand) {
        $isccPath = $isccCommand.Source
    }
}
if (-not $isccPath) {
    Write-Host "Inno Setup not found. The EXE was created successfully."
    Write-Host "The built EXE is here: $distDir\$appName.exe"
    exit 0
}

Write-Host "[3/3] Building installer..."
& $isccPath "$projectRoot\installer.iss"

if ($LASTEXITCODE -ne 0) {
    throw "Installer build failed."
}

Write-Host "Build finished."
Write-Host "EXE: $distDir\$appName.exe"
Write-Host "Installer: $projectRoot\Output\USB-Stick-Ersteller-Pro-Setup.exe"
