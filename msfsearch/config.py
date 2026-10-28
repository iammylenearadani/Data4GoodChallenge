"""All tunable knobs in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "D4GC data"          # contains Parsed/ and Original/
PARSED_DIR = DATA_DIR / "Parsed"
ORIGINAL_DIR = DATA_DIR / "Original"
CSV_PATH = ROOT / "data" / "documentation.csv"
ARTIFACTS = ROOT / "artifacts"

# --- cleaning
BOILERPLATE_MIN_DOCS = 5        # a line found in >= this many documents is website boilerplate
MIN_WORDS = 50                  # documents shorter than this after cleaning are dropped as junk
JUNK_IDENTICAL_MIN = 3          # cleaned text identical in >= this many docs -> failed scrape, dropped
KNOWN_BANNERS = [
    "this page is not available in this language", "aller au contenu principal", "skip to main content",
    "ir al contenido principal", "download on the app store", "get it on google play", "select language",
]

# --- families (duplicates / editions / translations)
COPY_SIM = 0.95                 # TF-IDF cosine >= this -> exact copy
EDITION_SIM = 0.80              # >= this AND similar titles -> edition of the same document
TITLE_SIM = 0.8                 # title word-overlap needed for an edition link (0.5 merged measles+cholera guides)
TRANSLATION_DENSE_SIM = 0.87    # + mutual nearest neighbour + same genre (families.py). Audit of all such pairs: >=0.87 are real EN<->AR/FR/ES translations

# --- chunking
CHUNK_WORDS = 250
CHUNK_OVERLAP = 50
MIN_CHUNK_WORDS = 30
HEAD_CHARS = 2000               # "title + abstract" field size

# --- dense retrieval (optional, needs sentence-transformers at build and query time)
EMBED_MODEL = "intfloat/multilingual-e5-small"   # 118M params, 384-dim, 100 languages, MIT licence
DENSE_MAX_CHUNKS_PER_DOC = 60   # caps embedding time for 300-page reports

# --- ranking
RRF_K = 60
CANDIDATES = 300
KEYWORD_CUTOFF = 0.45           # keep a doc if its best passage scores >= 45% of the best passage overall...
DENSE_MARGIN = 0.06             # ...or its dense cosine is within this of the best dense cosine
ABSTAIN_COVERAGE = 0.5          # abstain if < 50% of query words appear in the top doc...
ABSTAIN_DENSE = 0.81            # ...or (hybrid/dense) top dense cosine < this. Answerable min: manual 0.864, title set 0.817; no-answer 0.805-0.864
