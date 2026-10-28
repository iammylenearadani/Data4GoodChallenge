# Project structure

```
app.py               Streamlit entry point; one tab per feature
bedrock_helpers.py   All Bedrock access (chat, JSON, embeddings, RAG)
check_env.py         Credential + model smoke test
data/                Partner data (gitignored if sensitive)
notebooks/           Exploration only; nothing the demo depends on
prompts/             System prompts as .md files, loaded by app.py
```

## Conventions
- New feature = a new function in its own module (e.g. `triage.py`) + a tab in `app.py`
- Prompts live in `prompts/*.md`, not inline strings, so the strategist can edit them
- Small, working commits; keep `main` demo-ready at all times
