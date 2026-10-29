# Build the Windows app, then zip it for a GitHub Release.
#
#   .\commands\windows\build.ps1
#
# Result:
#   dist\UEFA-Simulator\UEFA-Simulator.exe     the app (NOT the one in build\)
#   dist\UEFA-Simulator-windows.zip            the zip to upload
Set-Location -Path (Join-Path $PSScriptRoot "..\..")

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") { $python = ".venv\Scripts\python.exe" }

# An old build that is still open (the app, an Explorer window, OneDrive syncing)
# cannot be deleted, and PyInstaller then stops with 'Access is denied'.
# So: close the app, delete the old build here, and explain if it fails.
Get-Process "UEFA-Simulator" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Milliseconds 500
if (Test-Path "dist\UEFA-Simulator") {
    Remove-Item -Recurse -Force "dist\UEFA-Simulator" -ErrorAction SilentlyContinue
    if (Test-Path "dist\UEFA-Simulator") {
        Write-Host "Could not delete the old build in dist\UEFA-Simulator: a file in it is in use." -ForegroundColor Red
        Write-Host "1. Close any File Explorer window open on that folder."
        Write-Host "2. The project is in OneDrive: pause syncing (OneDrive icon, Pause syncing), then try again."
        exit 1
    }
}

& $python -m pip install "pyinstaller>=6"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m PyInstaller --noconfirm UEFA-Simulator.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Zip the app. Right after the build, OneDrive or Windows Defender often holds
# a new file for a few seconds ("being used by another process"), and
# Compress-Archive then stops halfway. So: wait, try again, check that the zip
# really holds every file, and fall back to Windows' own tar.exe if needed.
$zip    = "dist\UEFA-Simulator-windows.zip"
$folder = "dist\UEFA-Simulator"

function Test-Zip {
    if (-not (Test-Path $zip)) { return $false }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    try {
        $archive = [System.IO.Compression.ZipFile]::OpenRead((Resolve-Path $zip).Path)
        $inZip = @($archive.Entries | Where-Object { $_.Name -ne "" }).Count
        $archive.Dispose()
    } catch { return $false }
    $onDisk = @(Get-ChildItem $folder -Recurse -File).Count
    return ($inZip -eq $onDisk)
}

$zipped = $false
for ($try = 1; $try -le 5 -and -not $zipped; $try++) {
    Start-Sleep -Seconds 3
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    try {
        Compress-Archive -Path $folder -DestinationPath $zip -Force -ErrorAction Stop
    } catch {
        Write-Host "Zip attempt $try of 5: a file is still in use, trying again..." -ForegroundColor Yellow
    }
    $zipped = Test-Zip
}

if (-not $zipped -and (Get-Command tar.exe -ErrorAction SilentlyContinue)) {
    Write-Host "Compress-Archive failed 5 times, trying tar.exe..." -ForegroundColor Yellow
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    tar.exe -a -c -f $zip -C dist UEFA-Simulator
    $zipped = Test-Zip
}

if (-not $zipped) {
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    Write-Host "The app is built in dist\UEFA-Simulator\, but it could not be zipped." -ForegroundColor Red
    Write-Host "1. Pause OneDrive syncing (OneDrive icon, Pause syncing)."
    Write-Host "2. Run only this line from the project folder:"
    Write-Host "   tar.exe -a -c -f dist\UEFA-Simulator-windows.zip -C dist UEFA-Simulator"
    exit 1
}

Write-Host ""
Write-Host "Done: dist\UEFA-Simulator-windows.zip" -ForegroundColor Green
