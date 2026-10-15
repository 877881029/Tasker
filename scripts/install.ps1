# Tasker quick installer / updater.
#
#   irm https://github.com/877881029/Tasker-releases/releases/latest/download/install.ps1 | iex
#
# Downloads the newest release, installs it to %LOCALAPPDATA%\Programs\Tasker,
# creates a desktop shortcut and starts Tasker. Task data in %LOCALAPPDATA%\Tasker is kept.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Repo = "877881029/Tasker-releases"
$Target = Join-Path $env:LOCALAPPDATA "Programs\Tasker"

Write-Host "Tasker: looking up the latest release..."
$Release = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "Tasker-installer" }
$Asset = $Release.assets | Where-Object { $_.name -like "Tasker-*-win64.zip" } | Select-Object -First 1
if (-not $Asset) { throw "No Tasker zip found in $($Release.tag_name)" }

$Work = Join-Path $env:TEMP "tasker-install-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $Work | Out-Null
try {
    $Zip = Join-Path $Work $Asset.name
    $SizeMb = [math]::Round($Asset.size / 1MB)
    Write-Host "Tasker: downloading $($Release.tag_name) ($SizeMb MB)..."
    Invoke-WebRequest $Asset.browser_download_url -OutFile $Zip -UseBasicParsing

    Write-Host "Tasker: unpacking..."
    $Unpacked = Join-Path $Work "unpacked"
    New-Item -ItemType Directory -Path $Unpacked | Out-Null
    $Tar = Get-Command tar.exe -ErrorAction SilentlyContinue
    if ($Tar) { & $Tar.Source -xf $Zip -C $Unpacked } else { Expand-Archive $Zip -DestinationPath $Unpacked }
    $Source = Join-Path $Unpacked "Tasker"
    if (-not (Test-Path (Join-Path $Source "Tasker.exe"))) { throw "Tasker.exe is missing from the download" }

    Get-Process Tasker -ErrorAction SilentlyContinue |
        Where-Object { $_.Path -and $_.Path.StartsWith($Target, [StringComparison]::OrdinalIgnoreCase) } |
        ForEach-Object { Stop-Process -Id $_.Id -Force }
    Start-Sleep -Milliseconds 800

    New-Item -ItemType Directory -Path $Target -Force | Out-Null
    robocopy $Source $Target /MIR /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "Copy to $Target failed (robocopy $LASTEXITCODE)" }

    $Exe = Join-Path $Target "Tasker.exe"
    $Desktop = [Environment]::GetFolderPath("Desktop")
    $Shell = New-Object -ComObject WScript.Shell
    $Link = $Shell.CreateShortcut((Join-Path $Desktop "Tasker.lnk"))
    $Link.TargetPath = $Exe
    $Link.WorkingDirectory = $Target
    $Link.IconLocation = (Join-Path $Target "_internal\assets\icons\tasker.ico") + ",0"
    $Link.Save()

    Start-Process $Exe
    Write-Host "Tasker $($Release.tag_name) installed to $Target and started. Desktop shortcut: Tasker."
} finally {
    Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
}
