"""Tiny Bedrock toolkit: chat, structured JSON, embeddings, mini-RAG.

Uses the Bedrock *Converse* API, so the same code works for any chat model
(Anthropic Claude, Amazon Nova, Llama, Mistral...) — just change BEDROCK_MODEL_ID.
"""
import json
import os
import re

import boto3
import numpy as np
from dotenv import load_dotenv

load_dotenv()

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "")
EMBED_ID = os.getenv("BEDROCK_EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")

_runtime = boto3.client("bedrock-runtime", region_name=REGION)


def chat(prompt, system="You are a helpful assistant.", history=None,
         model_id=None, max_tokens=1500, temperature=0.3):
    """One call to a chat model. history = [{"role": "user"|"assistant", "content": str}, ...]"""
    msgs = [{"role": m["role"], "content": [{"text": m["content"]}]} for m in (history or [])]
    msgs.append({"role": "user", "content": [{"text": prompt}]})
    resp = _runtime.converse(
        modelId=model_id or MODEL_ID,
        system=[{"text": system}],
        messages=msgs,
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    return resp["output"]["message"]["content"][0]["text"]


def chat_json(prompt, system="Reply with valid JSON only, no prose.", **kw):
    """Ask for JSON and parse it (tolerates ```json fences)."""
    raw = chat(prompt, system=system, temperature=0, **kw)
    m = re.search(r"\{.*\}|\[.*\]", raw, re.S)
    return json.loads(m.group(0) if m else raw)


def embed(texts):
    """Titan v2 embeddings -> np.ndarray (n, dim). One call per text (Titan has no batch)."""
    out = []
    for t in texts:
        body = json.dumps({"inputText": t[:8000], "normalize": True})
        r = _runtime.invoke_model(modelId=EMBED_ID, body=body)
        out.append(json.loads(r["body"].read())["embedding"])
    return np.array(out, dtype="float32")


class MiniRAG:
    """In-memory retrieval: good enough for a hackathon (a few thousand chunks)."""

    def __init__(self, docs, chunk_size=800, overlap=100):
        self.chunks = []
        for d in docs:
            for i in range(0, max(len(d), 1), chunk_size - overlap):
                self.chunks.append(d[i:i + chunk_size])
        self.vecs = embed(self.chunks)

    def search(self, query, k=4):
        q = embed([query])[0]
        scores = self.vecs @ q
        idx = np.argsort(-scores)[:k]
        return [(self.chunks[i], float(scores[i])) for i in idx]

    def answer(self, question, k=4):
        hits = self.search(question, k)
        context = "\n\n---\n\n".join(c for c, _ in hits)
        prompt = (f"Answer using ONLY the context. If the answer isn't there, say so.\n\n"
                  f"<context>\n{context}\n</context>\n\nQuestion: {question}")
        return chat(prompt), hits
