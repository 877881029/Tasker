# Build Tasker, publish it to the release repository and keep only the newest releases.
#
#   .\scripts\release.ps1               # build + publish the version in VERSION
#   .\scripts\release.ps1 -SkipBuild    # publish the existing dist\Tasker
#
# Requires: gh (logged in as an account that can write to $ReleaseRepo).
[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [string]$ReleaseRepo = "877881029/Tasker-releases",
    [int]$Keep = 5
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { throw "Run .\scripts\setup.ps1 -Dev first (.venv is missing)" }

& $Python scripts\bump_version.py --check
if ($LASTEXITCODE -ne 0) { throw "VERSION and version_info.txt disagree; run scripts\bump_version.py" }
$Version = (Get-Content (Join-Path $Root "VERSION") -Raw).Trim()
$Tag = "v$Version"

$Notes = & $Python -c @"
import re, sys
text = open('CHANGELOG.md', encoding='utf-8').read()
m = re.search(r'^## $([regex]::Escape($Version))\b.*?\n(.*?)(?=^## |\Z)', text, re.S | re.M)
sys.stdout.reconfigure(encoding='utf-8')
print(m.group(1).strip() if m else '')
"@
if (-not $Notes) { throw "CHANGELOG.md has no '## $Version' section" }

if (-not $SkipBuild) {
    # PyInstaller + WebEngine paths get long; build from a short drive letter.
    $Drive = @("T", "U", "V", "W", "X", "Y", "Z") | Where-Object { -not (Test-Path "$($_):\") } | Select-Object -First 1
    if (-not $Drive) { throw "No free drive letter for subst" }
    subst "$($Drive):" $Root
    try {
        & powershell -NoProfile -ExecutionPolicy Bypass -File "$($Drive):\scripts\build_windows.ps1"
        if ($LASTEXITCODE -ne 0) { throw "Build failed (exit $LASTEXITCODE)" }
    } finally {
        subst "$($Drive):" /D
    }
}

$Dist = Join-Path $Root "dist\Tasker"
if (-not (Test-Path (Join-Path $Dist "Tasker.exe"))) { throw "dist\Tasker\Tasker.exe is missing" }
$Zip = Join-Path $Root "dist\Tasker-$Version-win64.zip"
if (Test-Path $Zip) { Remove-Item $Zip }
& $Python -c "import shutil, sys; shutil.make_archive(sys.argv[1][:-4], 'zip', sys.argv[2], 'Tasker')" $Zip (Join-Path $Root "dist")
if ($LASTEXITCODE -ne 0) { throw "Failed to create $Zip" }
$Installer = Join-Path $Root "scripts\install.ps1"
$NotesFile = Join-Path $env:TEMP "tasker-release-notes.md"
$Install = "irm https://github.com/$ReleaseRepo/releases/latest/download/install.ps1 | iex"
@"
$Notes

---
**安装 / 升级**（PowerShell）：

``````powershell
$Install
``````

或下载 ``Tasker-$Version-win64.zip`` 解压后运行 ``Tasker\Tasker.exe``。数据在 ``%LOCALAPPDATA%\Tasker``，升级不会覆盖。
"@ | Set-Content -Encoding utf8 $NotesFile

gh release view $Tag -R $ReleaseRepo *> $null
if ($LASTEXITCODE -eq 0) { throw "$Tag already exists in $ReleaseRepo; bump the version first" }
gh release create $Tag $Zip $Installer -R $ReleaseRepo --title "Tasker $Version" --notes-file $NotesFile --latest
if ($LASTEXITCODE -ne 0) { throw "gh release create failed" }

$Releases = gh release list -R $ReleaseRepo --limit 100 --json tagName,createdAt | ConvertFrom-Json |
    Sort-Object { [datetime]$_.createdAt } -Descending
foreach ($Old in ($Releases | Select-Object -Skip $Keep)) {
    gh release delete $Old.tagName -R $ReleaseRepo --yes --cleanup-tag
}
Write-Host "Published $Tag to https://github.com/$ReleaseRepo/releases/tag/$Tag (keeping newest $Keep)"
