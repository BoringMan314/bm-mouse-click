param(
  [switch]$WithBuild,
  [string]$PyWin10 = "py -3.13",
  [string]$PyWin7 = "py -3.8"
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
  Write-Host ""
  Write-Host "==> $msg"
}

function Test-CommandExists([string]$cmd) {
  $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

Write-Step "Check required files"
$required = @(
  "main.py",
  "build.py",
  "build.ps1",
  "build_mac.sh",
  "requirements-win10.txt",
  "requirements-win7.txt",
  "README.md",
  "LICENSE"
)
foreach ($f in $required) {
  if (-not (Test-Path $f)) {
    throw "Missing required file: $f"
  }
}
Write-Host "Required files OK"

Write-Step "Python syntax check"
python -m py_compile main.py
Write-Host "Syntax OK: main.py"

Write-Step "Toolchain info"
if (Test-CommandExists "py") {
  py -0p
} else {
  Write-Host "Python launcher 'py' not found (fallback to explicit python paths if needed)."
}

if ($WithBuild) {
  Write-Step "Build verification (Win10/11 + Win7)"
  powershell -ExecutionPolicy Bypass -File .\build.ps1 -PyWin10 $PyWin10 -PyWin7 $PyWin7

  Write-Step "Verify output files"
  $outputs = @(
    "bm-mouse-click.exe",
    "bm-mouse-click_win7.exe"
  )
  foreach ($out in $outputs) {
    if (-not (Test-Path $out)) {
      throw "Build output missing: $out"
    }
  }
  Get-ChildItem $outputs | Select-Object Name, Length, LastWriteTime
}

Write-Host ""
Write-Host "Check completed successfully."
