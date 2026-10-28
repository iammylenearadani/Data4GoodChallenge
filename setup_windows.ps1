# One-command setup (PowerShell):  powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$py = "py -3.12"
try { & py -3.12 --version | Out-Null } catch { $py = "py -3.11" }
try { Invoke-Expression "$py --version" | Out-Null } catch { $py = "python" }
Write-Host "Using: $py"

Invoke-Expression "$py -m venv .venv"
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -r requirements.txt
& .\.venv\Scripts\python.exe -m ipykernel install --user --name d4gc --display-name "Python (d4gc)"

if (-not (Test-Path .env)) { Copy-Item .env.example .env }
Write-Host ""
Write-Host "Done. Activate with:  .\.venv\Scripts\Activate.ps1"
Write-Host "Smoke test:           python check_env.py"
Write-Host "Demo app:             streamlit run app.py"
