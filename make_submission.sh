#!/usr/bin/env bash
# Code ZIP for the jury: no secrets, no data, no virtualenv, no build artifacts.
cd "$(dirname "$0")"; rm -f submission.zip
zip -qr submission.zip . -x ".env" ".venv/*" "*/__pycache__/*" "__pycache__/*" "data/*" "artifacts/*" "node_modules/*" "dist/*" ".git/*" "submission.zip"
unzip -l submission.zip | grep -qE "(^|/)\.env$" && echo "WARNING: .env inside!" || echo "OK: submission.zip ($(du -h submission.zip | cut -f1)), no .env"
