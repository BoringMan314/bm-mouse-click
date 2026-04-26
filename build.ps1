param(
  [string]$PyWin10 = "py -3.13",
  [string]$PyWin7 = "py -3.8"
)

$ErrorActionPreference = "Stop"

function Ensure-CleanTempDirs {
  foreach ($d in @("build", "dist")) {
    $p = Join-Path $PSScriptRoot $d
    if (-not (Test-Path -LiteralPath $p)) {
      New-Item -ItemType Directory -Path $p | Out-Null
    }
    Get-ChildItem -LiteralPath $p -Force -ErrorAction SilentlyContinue | ForEach-Object {
      Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
  }
}

function Remove-OldExe {
  param([string]$OutputName)
  $exeName = "$OutputName.exe"
  $exePath = Join-Path $PSScriptRoot $exeName
  try {
    taskkill /F /IM $exeName /T *> $null
  } catch {}
  if (Test-Path -LiteralPath $exePath) {
    Remove-Item -LiteralPath $exePath -Force -ErrorAction Stop
    if (Test-Path -LiteralPath $exePath) {
      throw "Output exe is still locked: $exePath"
    }
  }
}

function Get-PythonVersionText {
  param([string]$PythonCmd)
  $cmd = "$PythonCmd -c `"import platform; print(platform.python_version())`""
  $output = $null
  try {
    $output = Invoke-Expression $cmd 2>$null
  } catch {
    throw "Cannot execute Python command: [$PythonCmd]. Please install the requested Python version first."
  }
  if ($LASTEXITCODE -ne 0 -or $null -eq $output -or [string]::IsNullOrWhiteSpace(($output | Out-String))) {
    throw "Cannot execute Python command: [$PythonCmd]. Please install the requested Python version first."
  }
  return (($output | Out-String).Trim())
}

function Assert-Win7PythonCompatible {
  param([string]$PythonCmd)
  $cmd = "$PythonCmd -c `"import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')`""
  $output = $null
  try {
    $output = Invoke-Expression $cmd 2>$null
  } catch {
    throw "Win7 build requires Python 3.8. Cannot execute: [$PythonCmd]"
  }
  if ($LASTEXITCODE -ne 0 -or $null -eq $output -or [string]::IsNullOrWhiteSpace(($output | Out-String))) {
    throw "Win7 build requires Python 3.8. Cannot execute: [$PythonCmd]"
  }
  $ver = (($output | Out-String).Trim())
  $parts = $ver.Split(".")
  if ($parts.Count -lt 2) {
    throw "Cannot parse Win7 Python version: $ver"
  }
  $major = [int]$parts[0]
  $minor = [int]$parts[1]
  if ($major -gt 3 -or ($major -eq 3 -and $minor -gt 8)) {
    throw "Win7 build must use Python 3.8 or lower. Current: $ver ($PythonCmd)"
  }
}

function Invoke-InVenv {
  param(
    [string]$PythonCmd,
    [string]$VenvDir,
    [string]$RequirementsFile,
    [string]$OutputName
  )

  $pythonVer = Get-PythonVersionText -PythonCmd $PythonCmd
  Write-Host "==> Build $OutputName with [$PythonCmd] (Python $pythonVer)"
  Remove-OldExe -OutputName $OutputName
  Ensure-CleanTempDirs
  $isWin7Chain = $OutputName -like "*_win7"
  Invoke-Expression "$PythonCmd -m venv `"$VenvDir`""
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create venv for $OutputName"
  }
  if ($isWin7Chain) {
    # Python 3.8 breaks with newer pip; keep a compatible pip line.
    & "$VenvDir\Scripts\python.exe" -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) {
      throw "Failed ensurepip for Win7 chain"
    }
    & "$VenvDir\Scripts\python.exe" -m pip install "pip<24.1" "setuptools<70" "wheel<0.44"
  } else {
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip
  }
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to prepare pip for $OutputName"
  }
  & "$VenvDir\Scripts\python.exe" -m pip install -r $RequirementsFile
  if ($LASTEXITCODE -ne 0) {
    throw "Failed dependency install for $OutputName"
  }
  & "$VenvDir\Scripts\pyinstaller.exe" `
    --noconfirm `
    --clean `
    --distpath "dist" `
    --onefile `
    --windowed `
    --noupx `
    --name $OutputName `
    --icon "icons/icon.ico" `
    --add-data "wav/switch.wav;wav" `
    main.py
  if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed for $OutputName"
  }
  $distExe = Join-Path (Join-Path $PSScriptRoot "dist") "$OutputName.exe"
  $rootExe = Join-Path $PSScriptRoot "$OutputName.exe"
  if (-not (Test-Path -LiteralPath $distExe)) {
    throw "Missing built exe in dist: $distExe"
  }
  Move-Item -LiteralPath $distExe -Destination $rootExe -Force
  Ensure-CleanTempDirs
}

Assert-Win7PythonCompatible -PythonCmd $PyWin7
Invoke-InVenv -PythonCmd $PyWin10 -VenvDir ".venv-build-win10" -RequirementsFile "requirements-win10.txt" -OutputName "bm-mouse-click"
Invoke-InVenv -PythonCmd $PyWin7 -VenvDir ".venv-build-win7" -RequirementsFile "requirements-win7.txt" -OutputName "bm-mouse-click_win7"

Write-Host ""
Write-Host "Build done. EXE paths:"
Write-Host "  .\bm-mouse-click.exe (Win10/11 chain)"
Write-Host "  .\bm-mouse-click_win7.exe (Win7 chain)"
