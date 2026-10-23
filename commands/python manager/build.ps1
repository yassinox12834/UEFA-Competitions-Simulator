# Build the Windows app with the Python version written in version.ps1,
# then zip it for a GitHub Release.
#
#   & ".\commands\python manager\build.ps1"
#
# Result:
#   dist\UEFA-Simulator\UEFA-Simulator.exe     the app (NOT the one in build\)
#   dist\UEFA-Simulator-windows.zip            the zip to upload
Set-Location -Path (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "version.ps1")

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

py "-$Version" -m pip install "pyinstaller>=6"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

py "-$Version" -m PyInstaller --noconfirm UEFA-Simulator.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Compress-Archive -Path "dist\UEFA-Simulator" -DestinationPath "dist\UEFA-Simulator-windows.zip" -Force
Write-Host ""
Write-Host "Done: dist\UEFA-Simulator-windows.zip" -ForegroundColor Green
