$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$VenvPath = if ($env:TASKER_BUILD_VENV) {
    [System.IO.Path]::GetFullPath($env:TASKER_BUILD_VENV)
} else {
    Join-Path $Root ".venv"
}
$PythonPath = Join-Path $VenvPath "Scripts\python.exe"

if (-not (Test-Path $PythonPath)) {
    py -3.12 -m venv $VenvPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create the Python virtual environment (exit $LASTEXITCODE)"
    }
}

$Python = Resolve-Path $PythonPath
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    throw "Failed to upgrade pip (exit $LASTEXITCODE)"
}
& $Python -m pip install -e ".[dev]" pyinstaller
if ($LASTEXITCODE -ne 0) {
    throw "Failed to install build dependencies (exit $LASTEXITCODE)"
}
& $Python scripts\generate_icons.py
if ($LASTEXITCODE -ne 0) {
    throw "Failed to generate application icons (exit $LASTEXITCODE)"
}

$DistPath = Join-Path $Root "dist"
$WorkPath = Join-Path $Root "build"
foreach ($Path in @($WorkPath, $DistPath)) {
    if (Test-Path $Path) {
        Remove-Item -Recurse -Force $Path
    }
}

& $Python -m PyInstaller tasker.spec --noconfirm --clean --distpath $DistPath --workpath $WorkPath
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed (exit $LASTEXITCODE)"
}

if (-not (Test-Path "dist\Tasker\Tasker.exe")) {
    throw "dist\Tasker\Tasker.exe was not produced"
}

$frozenIco = Join-Path $DistPath "Tasker\_internal\assets\icons\tasker.ico"
if (-not (Test-Path $frozenIco)) {
    throw "Frozen runtime resource is missing: Tasker\_internal\assets\icons\tasker.ico"
}

Write-Host "Built dist\Tasker\Tasker.exe"
