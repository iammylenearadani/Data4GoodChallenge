# Windows: powershell -ExecutionPolicy Bypass -File .\make_submission.ps1
Set-Location $PSScriptRoot
Remove-Item submission.zip -ErrorAction SilentlyContinue
$skip = '\\(\.venv|data|artifacts|__pycache__|\.git)\\|\\\.env$|submission\.zip$'
$files = Get-ChildItem -Recurse -File | Where-Object { ($_.FullName -replace [regex]::Escape($PSScriptRoot), '') -notmatch $skip }
Compress-Archive -Path $files.FullName -DestinationPath submission.zip
Write-Host "OK: submission.zip created without .env, data, artifacts, .venv"
