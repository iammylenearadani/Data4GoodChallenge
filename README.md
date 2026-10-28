# D4GC 2026 — AWS track starter kit

## Before you leave home (10 min)
1. Install **Python 3.12** (python.org) — 3.13 also works, avoid 3.14 for now.
2. Unzip this folder, open a terminal in it:
   - macOS/Linux: `bash setup_mac_linux.sh`
   - Windows: `powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1`
3. Everyone on the team does this — don't rely on one laptop.

## When the AWS workshop gives you an account (~10:00)
1. Workshop Studio → **Get AWS CLI credentials** → paste the 3 values into `.env`.
2. `python check_env.py` → copy a chat model id into `BEDROCK_MODEL_ID` in `.env` → re-run.
3. `streamlit run app.py` → you have a working demo shell.

## Files
| File | What |
|---|---|
| `bedrock_helpers.py` | `chat()`, `chat_json()`, `embed()`, `MiniRAG` — Bedrock Converse API, model-agnostic |
| `check_env.py` | Verifies credentials, lists usable models, makes a test call |
| `app.py` | Streamlit demo: data explorer / document Q&A / AI assistant tabs |
| `requirements.txt` | boto3, langchain-aws, faiss, pandas, sklearn, shap, plotly, streamlit, jupyter |

## If credentials expire mid-afternoon
Workshop Studio credentials are temporary. `ExpiredToken` → re-copy from Workshop Studio into `.env`, restart Streamlit.
