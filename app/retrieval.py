
from fastapi import APIRouter, HTTPException
from .models import AskIn, AskOut
from .chroma import coll
from app.settings import settings
from fastapi import Depends
from app.deps import get_logger, get_oa
from app.services.logger import LoggerService
from openai import OpenAI
import tiktoken

router = APIRouter()

from app.prompts.retrieval import RETRIEVAL_SYSTEM_PROMPT

def _get_token_count(text: str) -> int:
    enc = tiktoken.encoding_for_model(settings.OPENAI_EMBED_MODEL)
    return len(enc.encode(text))

def _embed(texts, oa, logger=None):
    MAX_TOKENS = 250000
    batches = []
    current_batch = []
    current_tokens = 0
    for t in texts:
        t_tokens = _get_token_count(t)
        if current_tokens + t_tokens > MAX_TOKENS and current_batch:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(t)
        current_tokens += t_tokens
    if current_batch:
        batches.append(current_batch)
    out = []
    for batch in batches:
        try:
            resp = oa.embeddings.create(model=settings.OPENAI_EMBED_MODEL, input=batch)
            out.extend([d.embedding for d in resp.data])
        except Exception as e:
            if logger:
                logger.error(f"Embedding failed: {e}")
            raise HTTPException(status_code=500, detail="Embedding failed.")
    return out

def _build_prompt(question: str, contexts):
    sections = []
    for c in contexts:
        meta = c.get("metadata", {})
        src = meta.get("source", "unknown")
        page = meta.get("page", None)
        where = f"{src}" + (f", p.{page}" if page else "")
        sections.append(f"{c['text']}\n(Source: {where})")
    ctx = "\n\n".join(sections)
    return (
        f"Answer the question using ONLY the context.\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{ctx}\n\n"
        f"Instructions:\n"
        f"- If uncertain, say you don't know from these documents.\n"
        f"- Add a one-line disclaimer if health/contraindications are discussed.\n\n"
        f"Answer:\n"
    )

# --- Route ---
@router.post("/ask", response_model=AskOut)
def ask(
    payload: AskIn,
    logger: LoggerService = Depends(get_logger),
    oa: OpenAI = Depends(get_oa),
):
    k = payload.k or settings.TOP_K
    try:
        qvecs = _embed([payload.question], oa, logger)
        if not qvecs:
            raise HTTPException(status_code=400, detail="Failed to embed question.")
        qvec = qvecs[0]
        res = coll.query(query_embeddings=[qvec], n_results=k, where=payload.where or None)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Retrieval failed.")

    contexts = [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
    if not contexts:
        return AskOut(answer="I couldn't find anything in the current index.")

    prompt = _build_prompt(payload.question, contexts)

    try:
        chat = oa.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": RETRIEVAL_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        answer = chat.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Chat completion failed: {e}")
        raise HTTPException(status_code=500, detail="Chat completion failed.")

    return AskOut(answer=answer)
