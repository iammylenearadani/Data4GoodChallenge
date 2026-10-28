"""Text utilities shared by build and search: tokenizer (Arabic-safe, accent-insensitive), language guess, snippets."""
import re
import unicodedata

_token_re = re.compile(r"\w+", re.UNICODE)

STOP = {
    "en": set("the a an and or of to in on for with by is are was were be this that these those what how which when where who "
              "do does can should i we you it as at from about into not no".split()),
    "fr": set("le la les un une des et ou de du dans sur pour avec par est sont ce cette ces que qui quoi comment quand "
              "au aux en ne pas se".split()),
    "es": set("el la los las un una unos unas y o de del en sobre para con por es son este esta estos que quien como "
              "cuando al no se".split()),
}
ALL_STOP = set().union(*STOP.values())


def fold(text):
    """Lowercase and strip accents but keep non-Latin scripts (Arabic) intact."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def tokenize(text):
    return [t for t in _token_re.findall(fold(text)) if len(t) > 1]


def content_words(text):
    return [t for t in tokenize(text) if t not in ALL_STOP]


def detect_lang(text):
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    toks = tokenize(text)
    votes = {lang: sum(t in sw for t in toks) for lang, sw in STOP.items()}
    best = max(votes, key=votes.get)
    return best if votes[best] > 0 else "en"


def best_sentences(text, query, n=2):
    """Extractive snippet: sentences sharing most content words with the query (never invents text)."""
    q = set(content_words(query))
    sents = [s.strip() for s in re.split(r"(?<=[.!?؟])\s+|\n", text) if 25 < len(s.strip()) < 600]
    scored = sorted(sents, key=lambda s: -len(q & set(tokenize(s))))
    out = [s for s in scored[:n] if q & set(tokenize(s))]
    return out or sents[:1]
