#!/usr/bin/env bash
# Creates submission.zip without secrets, virtualenvs or big data folders.
cd "$(dirname "$0")"
rm -f submission.zip
zip -qr submission.zip . -x ".env" ".venv/*" "*/__pycache__/*" "data/*" "*.pkl.gz" ".git/*" "submission.zip"
echo "submission.zip: $(du -h submission.zip | cut -f1)"; unzip -l submission.zip | grep -E "\.env$" && echo "WARNING: .env inside!" || echo "OK: no .env inside"
