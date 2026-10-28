"""Decision card (on-premises): turn the top search results into 3-5 ACTION points for a field team leader.

Nothing is generated: every point is a sentence quoted exactly from an MSF document, with its source.
Sentences are ranked by: query words they contain + prescriptive wording ("must", "if", "within", "il faut", ...)
+ action verbs + numbers/doses/thresholds, with MSF clinical guidelines ranked above news and reports.
"""
import re
import unicodedata

from . import search as S
from .text import content_words, tokenize

# Scope: the outbreak / field team leader. Operational knowledge only (no finance, legal, speeches, history).
FIELD_GENRES = {
    "Clinical Guideline Chapter", "Peer-reviewed Article", "Field Study", "Operational Research Essay",
    "Project Update", "Evaluation Report", "Activity Report Chapter", "Press Release", "Summary", "Report",
    "First-person Field Account", "Voices from the Field", "Scientific Publication Notice",
}

_PRESCRIPTIVE = re.compile(
    r"\b(should|must|is essential|it is important|are required|is required|recommended|do not|never|avoid|ensure|"
    r"if|when|within|at least|as soon as|priorit\w*|"
    r"doit|doivent|il faut|faut|recommand[ée]e?s?|ne pas|[ée]viter|si|lorsque|d[eè]s que|au moins|imp[ée]ratif|"
    r"debe|deben|se recomienda|recomendad[oa]s?|no se debe|evitar|cuando|al menos)\b", re.I)
_ACTION = re.compile(r"\b(vaccinat\w*|treat\w*|isolat\w*|refer\w*|rehydrat\w*|chlorinat\w*|disinfect\w*|"
                     r"vaccin\w*|trait\w*|isol\w*|r[ée]hydrat\w*|chlor\w*|vacun\w*|trat\w*|aisl\w*)\b", re.I)
_UNITS = re.compile(r"\d[\d\s.,]*\s?(%|mg|ml|kg|g\b|l\b|litres?|liters?|hours?|h\b|days?|jours?|d[ií]as|weeks?|"
                    r"cases?|cas\b|casos|beds?|lits?|km|per\s?\d+|/\s?\d+)", re.I)
_JUNK = re.compile(r"et al\.|doi|https?://|www\.|©|\bpp?\.\s?\d|\[\d+\]|\bcitation\b|×|droits de|rights reserved|"
                   r"\d{4};\s?\d|cohort study\.?$|trial\.?$|Table \d|Figure \d|Fig\. ?\d", re.I)
# guideline front matter is not evidence (authors, prefaces, abbreviations, references...)
_FRONT = re.compile(r"^(abbreviations?|abr[ée]viations?|abreviaturas|authors?|auteurs|autores|acknowledg|remerciements|"
                    r"agradecimientos|preface|pr[ée]face|pr[oó]logo|foreword|avant-propos|main references|principales "
                    r"r[ée]f[ée]rences|use of the guide|utili[sz]ation de la gu|utilizaci[oó]n de la gu|appendices|annexes|"
                    r"anexos|introduction|introducci[oó]n|film:)", re.I)
_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9«\"(])|\n+")
_WRAP = re.compile(r"(?<![.!?:;\n])\n(?!\n|\s*[-*•#>|]|\s*\d+[.)]\s)")  # a PDF line wrap inside a sentence


def _sentences(text):
    for s in _SPLIT.split(_WRAP.sub(" ", text)):
        # PDF ligatures: "eﬃcacy" (NFKC) and "e\x81cacy" (this corpus encodes "ffi" as 0x81) -> "efficacy"
        s = unicodedata.normalize("NFKC", s.replace("\x81", "ffi")).replace("**", "")
        s = "".join(ch for ch in s if unicodedata.category(ch) not in ("Cc", "Co"))  # other invisible PDF junk
        s = re.sub(r"\s+", " ", re.sub(r"^[\s>*#\-–•·\d.)]+", "", s)).strip()
        s = re.sub(r"(?<=[a-z])- (?=[a-z])", "", s)  # PDF hyphenation: "cover- age" -> "coverage"
        if 7 <= len(s.split()) <= 55 and not _JUNK.search(s) and s[-1] in ".!?:;)":
            yield s


def action_points(query, results, n=5, per_doc=2):
    """results: search()['results'] (best first) -> list of quoted action sentences with their source."""
    docs = S.load()["docs"].set_index("doc_id")
    qw = set(content_words(query))
    cands = []
    for rank, r in enumerate(results[:4]):
        title = str(r["title"]).lower().strip(" .")
        seen = set()
        for s in _sentences(docs.loc[r["doc_id"], "text"][:300000]):
            key = s.lower().strip(" .")
            overlap = len(qw & set(tokenize(s)))
            if not overlap or key in seen or key == title:
                continue
            seen.add(key)
            score = (1.5 * overlap + 3.0 * bool(_PRESCRIPTIVE.search(s)) + 0.7 * bool(_ACTION.search(s))
                     + 2.0 * bool(_UNITS.search(s)) + 2.0 * (r["genre"] == "Clinical Guideline Chapter") - 0.3 * rank)
            cands.append((score, s, r))
    cands.sort(key=lambda c: -c[0])
    out, used = [], {}
    for score, s, r in cands:
        if used.get(r["doc_id"], 0) >= per_doc:
            continue
        used[r["doc_id"]] = used.get(r["doc_id"], 0) + 1
        out.append({"text": s, "doc_id": r["doc_id"], "title": r["title"], "year": r["year"],
                    "lang": r["lang"], "url": r["url"], "genre": r["genre"]})
        if len(out) >= n:
            break
    return out


def decide(query, k=5, mode="hybrid"):
    """Search within the field scope (no front matter), then build the decision card."""
    r = S.search(query, k=k + 5, genres=sorted(FIELD_GENRES), mode=mode)
    r["results"] = [x for x in r["results"] if not _FRONT.search(str(x["title"]).strip())][:k]
    r["actions"] = [] if r["abstained"] else action_points(query, r["results"])
    return r
