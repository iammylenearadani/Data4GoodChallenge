"""Ablation + threshold sweeps on hybrid mode -> printed table (nothing is written).

    python eval/sweep.py

Change config.py only when the title set AND the manual set agree; improving only the manual set is overfitting.
Ablation removes a list from the RRF fusion; the evidence filter still sees all signals.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import config as C  # noqa: E402
from msfsearch import search as S  # noqa: E402
from run_eval import HERE, evaluate, title_set  # noqa: E402

docs = S.load()["docs"]
sets = {"title": title_set(docs), "manual": pd.read_csv(HERE / "queries_manual.csv")}


def run(label):
    for name, qs in sets.items():
        r = evaluate(qs, "hybrid", docs)
        print(f"{label:30s} {name:6s}  Hit@1 {r['Hit@1']:>6}  Hit@5 {r['Hit@5']:>6}  MRR {r['MRR']}  "
              f"results {r['avg results']}  no-answer {r['abstains on no-answer']:>4}  "
              f"wrong-abst {r['wrong abstentions']}")


if not S.dense_ready():
    sys.exit("dense index not built: run `python -m msfsearch.build` with sentence-transformers installed")
base = (C.SIGNALS, C.KEYWORD_CUTOFF, C.DENSE_MARGIN, C.ABSTAIN_DENSE)
run("baseline")
print("\n# ablation: what each signal adds")
for drop in base[0]:
    C.SIGNALS = tuple(s for s in base[0] if s != drop)
    run(f"without {drop}")
C.SIGNALS = base[0]
print("\n# evidence filter: fewer results per query = fewer false positives")
for kc in (0.45, 0.55, 0.65):
    for dm in (0.03, 0.045, 0.06):
        C.KEYWORD_CUTOFF, C.DENSE_MARGIN = kc, dm
        run(f"cutoff {kc} margin {dm}")
C.KEYWORD_CUTOFF, C.DENSE_MARGIN = base[1], base[2]
print("\n# abstention threshold")
for t in (0.80, 0.81, 0.82, 0.83, 0.84):
    C.ABSTAIN_DENSE = t
    run(f"ABSTAIN_DENSE {t}")
