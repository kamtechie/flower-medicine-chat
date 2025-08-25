import uuid
from typing import List, Dict, Any
from .config import CHUNK_CHARS, CHUNK_OVERLAP, OPENAI_EMBED_MODEL
import tiktoken

def _chunk_text(text: str, source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + CHUNK_CHARS)
        chunk = text[i:j]
        if chunk.strip():
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": source_meta.copy()
            })
        i += CHUNK_CHARS - CHUNK_OVERLAP
        if i <= 0:
            break
    return chunks

def _get_token_count(text: str) -> int:
    enc = tiktoken.encoding_for_model(OPENAI_EMBED_MODEL)
    return len(enc.encode(text))
