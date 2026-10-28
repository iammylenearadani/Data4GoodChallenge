# Tech stack (fixed — do not introduce new frameworks)

- Python 3.12, virtualenv in `.venv`, dependencies in `requirements.txt` (add a line there if you add a package)
- UI: Streamlit (`app.py`), charts with Plotly
- LLM: Amazon Bedrock via `bedrock_helpers.py` — use `chat()`, `chat_json()`, `embed()`, `MiniRAG`. Do not call boto3 directly elsewhere.
- Model id and region come from `.env` (`BEDROCK_MODEL_ID`, `AWS_DEFAULT_REGION`); never hard-code them, never print or commit credentials
- Data: pandas; ML only if needed: scikit-learn + shap
- Everything must run locally with `streamlit run app.py` — no deployment, no Docker, no databases

## Constraints
- 4-hour build window: prefer the simplest thing that works; no premature abstraction
- Every Bedrock call wrapped so the UI shows a friendly error instead of a stack trace
- Cache expensive calls with `st.cache_data` / `st.session_state` so the live demo is fast
- No personal or regulated data (GDPR) in the AWS workshop account
