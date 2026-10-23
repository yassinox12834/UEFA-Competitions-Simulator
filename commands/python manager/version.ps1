# The Python version used by req.ps1, run.ps1 and build.ps1 in this folder.
#
# 1. Type  py --list  to see the versions installed on your computer.
# 2. Replace 3.12 below by one of them (3.10 or newer), for example 3.14.
#
# This is the only line to change: the three scripts read it from here.
$Version = "3.14"


# --- Do not change below: checks that this version exists. ---------------
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Host "The 'py' command was not found. Install Python from https://www.python.org/downloads/" -ForegroundColor Red
    Write-Host "or use the scripts in commands\windows instead."
    exit 1
}
py "-$Version" -c "pass" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python $Version is not installed on this computer." -ForegroundColor Red
    Write-Host "Your versions (py --list):"
    py --list
    Write-Host "Put one of them in commands\python manager\version.ps1, then try again."
    exit 1
}
