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

function Get-LatestTag {
    # Follow the web redirect /releases/latest -> /releases/tag/<tag>; unlike the REST API
    # this has no per-IP rate limit, which shared office networks hit quickly.
    $request = [System.Net.HttpWebRequest]::Create("https://github.com/$Repo/releases/latest")
    $request.Method = "HEAD"
    $request.AllowAutoRedirect = $false
    $request.UserAgent = "Tasker-installer"
    $response = $request.GetResponse()
    try {
        $location = $response.Headers["Location"]
    } finally {
        $response.Close()
    }
    if (-not $location -or $location -notmatch "/releases/tag/(?<tag>[^/?#]+)") {
        throw "Could not find the latest Tasker release"
    }
    return $Matches["tag"]
}

Write-Host "Tasker: looking up the latest release..."
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
$Tag = Get-LatestTag
$Version = $Tag.TrimStart("v")
$AssetName = "Tasker-$Version-win64.zip"
$AssetUrl = "https://github.com/$Repo/releases/download/$Tag/$AssetName"

$Work = Join-Path $env:TEMP "tasker-install-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $Work | Out-Null
try {
    $Zip = Join-Path $Work $AssetName
    Write-Host "Tasker: downloading $Tag (about 210 MB)..."
    Invoke-WebRequest $AssetUrl -OutFile $Zip -UseBasicParsing

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
    Write-Host "Tasker $Tag installed to $Target and started. Desktop shortcut: Tasker."
} finally {
    Remove-Item $Work -Recurse -Force -ErrorAction SilentlyContinue
}
