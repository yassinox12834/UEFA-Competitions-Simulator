# Install the packages. Run it once, then launch the app with run.ps1.
#
#   .\commands\windows\req.ps1
#
# The packages go into a virtual environment, the .venv folder in the project,
# so they never clash with the rest of your computer. The first run creates it.
Set-Location -Path (Join-Path $PSScriptRoot "..\..")

$venvPython = ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Python was not found." -ForegroundColor Red
        Write-Host "Install Python 3.10 or newer from https://www.python.org/downloads/"
        Write-Host "and tick 'Add python.exe to PATH' in the installer, then try again."
        exit 1
    }
    Write-Host "Creating the virtual environment (.venv)..." -ForegroundColor Cyan
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "Installing the packages..." -ForegroundColor Cyan
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Launch the app with:  .\commands\windows\run.ps1" -ForegroundColor Green
