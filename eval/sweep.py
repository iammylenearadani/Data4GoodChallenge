"""Ablation + threshold sweep on the TUNING set and the title set (never on the held-out set).
    python eval/sweep.py
Requires msfsearch/search.py to honour config.SIGNALS (see CLAUDE.md). Choose values only if both sets agree."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import config as C  # noqa: E402
from msfsearch import search as S  # noqa: E402
from run_eval import HERE, evaluate, title_set  # noqa: E402

docs = S.load()["docs"]
sets = {"title": title_set(docs), "tuning": pd.read_csv(HERE / "queries_manual.csv")}
mode = "hybrid" if S.dense_ready() else "keyword"


def run(label):
    for name, qs in sets.items():
        r = evaluate(qs, mode, docs)
        print(f"{label:34s} {name:7s} Hit@1 {r['Hit@1 strict']:>6}  Hit@5 {r['Hit@5 strict']:>6}  "
              f"results {r['avg results']}  no-ans {r['no-answer abstained']:>4}  wrong-abst {r['wrong abstentions']}")


signals = getattr(C, "SIGNALS", ("passage", "abstract", "dense"))
base = (signals, C.KEYWORD_CUTOFF, C.DENSE_MARGIN, C.ABSTAIN_DENSE)
run("baseline")
for drop in signals:
    C.SIGNALS = tuple(s for s in signals if s != drop)
    run(f"without {drop}")
C.SIGNALS = signals
for kc in (0.45, 0.55, 0.65):
    for dm in (0.03, 0.045, 0.06):
        C.KEYWORD_CUTOFF, C.DENSE_MARGIN = kc, dm
        run(f"cutoff {kc} margin {dm}")
C.KEYWORD_CUTOFF, C.DENSE_MARGIN = base[1], base[2]
for t in (0.79, 0.80, 0.81, 0.82, 0.83):
    C.ABSTAIN_DENSE = t
    run(f"ABSTAIN_DENSE {t}")
