"""Sync manifest: WHEN the library was built off-prem / pulled onto this field box, and WHETHER it is intact.

    python -m msfsearch.manifest          # stamp a pull (run on the box after copying a new artifacts/ folder)

build.py writes it automatically. The app shows "last synced … ago" and verifies the SHA-256 fingerprints,
so a field team knows how old its library is and that nobody altered it (MSF can be targeted).
"""
import hashlib
import json
import time

from . import config as C

FILES = ("index.pkl", "emb.f16.npy")
PATH = C.ARTIFACTS / "manifest.json"
FMT = "%Y-%m-%d %H:%M"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(built_at=None, n_docs=None):
    now = time.strftime(FMT)
    m = {"built_at": built_at or now, "pulled_at": now, "n_docs": n_docs,
         "source": "MSF document library, built off-premises",
         "sha256": {f: _sha256(C.ARTIFACTS / f) for f in FILES if (C.ARTIFACTS / f).exists()}}
    PATH.write_text(json.dumps(m, indent=1), encoding="utf-8")
    return m


def check():
    """-> manifest dict + 'verified' (bool) + 'age_days' (float), or None if the library was never stamped."""
    if not PATH.exists():
        return None
    m = json.loads(PATH.read_text(encoding="utf-8"))
    m["verified"] = all((C.ARTIFACTS / f).exists() and _sha256(C.ARTIFACTS / f) == h for f, h in m["sha256"].items())
    m["age_days"] = (time.time() - time.mktime(time.strptime(m["pulled_at"], FMT))) / 86400
    return m


if __name__ == "__main__":
    import pickle
    with open(C.ARTIFACTS / "index.pkl", "rb") as fh:
        pack = pickle.load(fh)
    m = write(pack.get("built"), len(pack["docs"]))
    print(f"[manifest] built {m['built_at']}, pulled {m['pulled_at']}, {m['n_docs']} docs, "
          f"sha256 {', '.join(f'{k}={v[:12]}' for k, v in m['sha256'].items())}")
