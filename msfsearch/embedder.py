"""Optional dense (semantic) embeddings with a small multilingual open model (default: multilingual-e5-small, MIT).

Used off-prem to embed passages, and on-prem to embed the query (one ~120 MB model, CPU is enough).
If sentence-transformers or the model is unavailable, everything falls back to keyword search.
"""
import numpy as np

from . import config as C

_model = None


def available():
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _get():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(C.EMBED_MODEL, device="cpu")
    return _model


def embed_passages(texts, batch_size=32):
    m = _get()
    v = m.encode([f"passage: {t}" for t in texts], batch_size=batch_size, normalize_embeddings=True,
                 show_progress_bar=True, convert_to_numpy=True)
    return v.astype(np.float16)


def embed_query(text):
    v = _get().encode([f"query: {text}"], normalize_embeddings=True, convert_to_numpy=True)[0]
    return v.astype(np.float32)
