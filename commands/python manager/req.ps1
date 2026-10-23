# Install the packages with the Python version written in version.ps1.
#
#   & ".\commands\python manager\req.ps1"
Set-Location -Path (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "version.ps1")

Write-Host "Installing the packages for Python $Version..." -ForegroundColor Cyan
py "-$Version" -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Done. Launch the app with:  & "".\commands\python manager\run.ps1""" -ForegroundColor Green
