import uuid
from typing import List, Dict, Any
from app.core.settings import settings
import tiktoken

def _chunk_text(text: str, source_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        j = min(n, i + settings.CHUNK_CHARS)
        chunk = text[i:j]
        if chunk.strip():
            chunks.append({
                "id": str(uuid.uuid4()),
                "text": chunk,
                "metadata": source_meta.copy()
            })
        i += settings.CHUNK_CHARS - settings.CHUNK_OVERLAP
        if i <= 0:
            break
    return chunks

def _get_token_count(text: str) -> int:
    enc = tiktoken.encoding_for_model(settings.OPENAI_EMBED_MODEL)
    return len(enc.encode(text))
