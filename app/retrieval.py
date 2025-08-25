from fastapi import APIRouter
from .models import AskIn, AskOut
from .chroma import coll
from .config import TOP_K, OPENAI_EMBED_MODEL, OPENAI_CHAT_MODEL
from openai import OpenAI

router = APIRouter()

SYSTEM_PROMPT = (
    "You are a careful assistant answering only from provided context about flower medicine "
    "and related material. If the answer is not in the context, say you don't know. "
    "Never provide diagnosis or treatment. Include concise citations like [1], [2] "
    "that map to sources. If health/contraindications appear, add a one-line disclaimer."
)

@router.post("/ask", response_model=AskOut)
def ask(payload: AskIn):
    oa = OpenAI()
    k = payload.k or TOP_K
    def _embed(texts):
        import tiktoken
        def _get_token_count(text: str) -> int:
            enc = tiktoken.encoding_for_model(OPENAI_EMBED_MODEL)
            return len(enc.encode(text))
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
            resp = oa.embeddings.create(model=OPENAI_EMBED_MODEL, input=batch)
            out.extend([d.embedding for d in resp.data])
        return out

    qvec = _embed([payload.question])[0]
    res = coll.query(query_embeddings=[qvec], n_results=k, where=payload.where or None)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    contexts = [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
    if not contexts:
        return AskOut(answer="I couldn't find anything in the current index.", citations=[])

    def _build_prompt(question: str, contexts):
        numbered_sections = []
        for i, c in enumerate(contexts, start=1):
            meta = c.get("metadata", {})
            src = meta.get("source", "unknown")
            page = meta.get("page", None)
            where = f"{src}" + (f", p.{page}" if page else "")
            numbered_sections.append(f"[{i}] {c['text']}\n(Source: {where})")
        ctx = "\n\n".join(numbered_sections)
        return (
            f"Answer the question using ONLY the context.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{ctx}\n\n"
            f"Instructions:\n"
            f"- Cite passages with [n] where n corresponds to the sources list above.\n"
            f"- If uncertain, say you don't know from these documents.\n"
            f"- Add a one-line disclaimer if health/contraindications are discussed.\n\n"
            f"Answer:\n"
        )

    prompt = _build_prompt(payload.question, contexts)

    chat = oa.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    answer = chat.choices[0].message.content

    citations = []
    for i, m in enumerate(metas, start=1):
        src = m.get("source", "unknown")
        page = m.get("page")
        citations.append({"n": str(i), "source": f"{src}" + (f", p.{page}" if page else "")})

    return AskOut(answer=answer, citations=citations)
