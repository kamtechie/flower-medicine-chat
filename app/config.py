import os
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logger = logging.getLogger("ingest")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "flower_medicine")
TOP_K = int(os.getenv("TOP_K", "8"))
CHUNK_CHARS = int(os.getenv("CHUNK_CHARS", "1800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "250"))
