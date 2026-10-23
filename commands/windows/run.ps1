# Launch the app.
#
#   .\commands\windows\run.ps1
#
# Uses the .venv folder made by req.ps1. Without it, uses the Python on your PATH.
Set-Location -Path (Join-Path $PSScriptRoot "..\..")

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") { $python = ".venv\Scripts\python.exe" }
elseif (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python was not found. Install it, then run .\commands\windows\req.ps1" -ForegroundColor Red
    exit 1
}

# Check the packages first: a clear message is better than a long error.
& $python -c "import tkinter, customtkinter, PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "The packages are missing. Run this first:  .\commands\windows\req.ps1" -ForegroundColor Red
    exit 1
}

& $python main.py
exit $LASTEXITCODE
