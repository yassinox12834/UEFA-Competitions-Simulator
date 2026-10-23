# Launch the app with the Python version written in version.ps1.
#
#   & ".\commands\python manager\run.ps1"
Set-Location -Path (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "version.ps1")

# Check the packages first: a clear message is better than a long error.
py "-$Version" -c "import tkinter, customtkinter, PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "The packages are missing for Python $Version. Run this first:" -ForegroundColor Red
    Write-Host "  & "".\commands\python manager\req.ps1"""
    exit 1
}

py "-$Version" main.py
exit $LASTEXITCODE
