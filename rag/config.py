"""RAG configuration: persistent storage paths, model names, and collection identifiers."""
import os
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = ROOT / ".runtime"
CHROMA_PERSIST_DIR = RUNTIME_DIR / "chroma"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

COLLECTION_FIXED = "medantrik_fixed_overlap"
COLLECTION_SENTENCE = "medantrik_sentence_based"

DEFAULT_TOP_K = 3


def ensure_runtime_dirs():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
