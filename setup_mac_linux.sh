#!/usr/bin/env bash
# One-command setup: bash setup_mac_linux.sh
set -e
cd "$(dirname "$0")"

PY=python3
for v in python3.12 python3.11; do command -v $v >/dev/null && PY=$v && break; done
echo "Using $($PY --version)"

$PY -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m ipykernel install --user --name d4gc --display-name "Python (d4gc)"

[ -f .env ] || cp .env.example .env
echo ""
echo "Done. Activate with:  source .venv/bin/activate"
echo "Smoke test:           python check_env.py"
echo "Demo app:             streamlit run app.py"
