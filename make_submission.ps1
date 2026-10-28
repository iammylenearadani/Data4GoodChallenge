# Windows: powershell -ExecutionPolicy Bypass -File .\make_submission.ps1
Set-Location $PSScriptRoot
Remove-Item submission.zip -ErrorAction SilentlyContinue
$skip = '\\(\.venv|data|artifacts|__pycache__|\.git|node_modules|dist)\\|\\\.env$|\.zip$'
$files = Get-ChildItem -Recurse -File -Force | Where-Object { ($_.FullName.Substring($PSScriptRoot.Length)) -notmatch $skip }
# copy into a staging folder first so the zip keeps the folder structure (msfsearch/, eval/, src/ ...)
$stage = Join-Path $env:TEMP "msf-submission"
Remove-Item $stage -Recurse -Force -ErrorAction SilentlyContinue
foreach ($f in $files) {
    $dest = Join-Path $stage $f.FullName.Substring($PSScriptRoot.Length + 1)
    New-Item -ItemType Directory -Force (Split-Path $dest) | Out-Null
    Copy-Item $f.FullName $dest
}
Compress-Archive -Path (Join-Path $stage "*") -DestinationPath submission.zip
Remove-Item $stage -Recurse -Force
Write-Host "OK: submission.zip created without .env, data, artifacts, .venv, node_modules"
