import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from chromadb import PersistentClient
from chromadb.config import Settings
from pydantic import BaseModel

from pypdf import PdfReader
from io import BytesIO

from openai import OpenAI
import tiktoken

# ---------- Logging ----------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("ingest")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

# ---------- Config ----------
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "flower_medicine")
TOP_K = int(os.getenv("TOP_K", "8"))
CHUNK_CHARS = int(os.getenv("CHUNK_CHARS", "1800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "250"))

# ---------- Clients ----------
oa = OpenAI()  # needs OPENAI_API_KEY in env
chroma = PersistentClient(path="./chroma")
coll = chroma.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

# ---------- FastAPI ----------
app = FastAPI(title="Flower Medicine RAG (Chroma + FastAPI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------- Models ----------
class AskIn(BaseModel):
    question: str
    where: Optional[Dict[str, Any]] = None  # e.g., {"book_title": "Bach ..."}
    k: Optional[int] = None

class AskOut(BaseModel):
    answer: str
    citations: List[Dict[str, str]]


# ---------- Utilities ----------
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
        if i <= 0:  # just in case of tiny CHUNK_CHARS
            break
    return chunks

def _pdf_to_texts(pdf_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    reader = PdfReader(BytesIO(pdf_bytes))
    items = []
    for p, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception as e:
            logger.warning("PDF text extraction error on %s page %d: %s", filename, p, e)
            txt = ""
        if txt.strip():
            items.extend(_chunk_text(
                txt,
                {"source": filename, "page": p}
            ))
    return items

def _embed(texts: List[str]) -> List[List[float]]:
    # OpenAI embedding API; returns 1536-d for text-embedding-3-small
    # Batch up texts so no batch exceeds 300,000 tokens, then fire off all batches
    MAX_TOKENS = 300000
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
    if len(batches) > 1:
        logger.info(f"Embedding request split into {len(batches)} batches due to token limit.")
    out = []
    for batch in batches:
        resp = oa.embeddings.create(model=OPENAI_EMBED_MODEL, input=batch)
        out.extend([d.embedding for d in resp.data])
    return out

def _get_token_count(text: str) -> int:
    enc = tiktoken.encoding_for_model(OPENAI_EMBED_MODEL)
    return len(enc.encode(text))

def _is_duplicate_chunk(chunk_text: str, source_meta: dict) -> bool:
    # Embed the chunk text using the same model as the collection
    embedding = _embed([chunk_text])[0]
    results = coll.query(query_embeddings=[embedding], where={"source": source_meta.get("source")}, n_results=1)
    docs = results.get("documents", [[]])[0]
    return any(doc == chunk_text for doc in docs)

# ---------- Ingestion ----------
@app.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    t0 = time.time()
    fname = file.filename
    try:
        data = await file.read()
        size_kb = len(data) / 1024.0
        logger.info("Ingest PDF start: %s (%.1f KB)", fname, size_kb)

        chunks = _pdf_to_texts(data, fname)
        if not chunks:
            logger.warning("Ingest PDF: no extractable text in %s", fname)
            return JSONResponse({"ok": False, "msg": "No extractable text found."}, status_code=400)

        ids = []
        docs = []
        metas = []
        for c in chunks:
            if not _is_duplicate_chunk(c["text"], c["metadata"]):
                ids.append(c["id"])
                docs.append(c["text"])
                metas.append(c["metadata"])
        if not docs:
            logger.info("All chunks for %s are duplicates, skipping.", fname)
            return JSONResponse({"ok": False, "msg": "All chunks are duplicates."}, status_code=200)
        vecs = _embed(docs)
        coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)

        dt = time.time() - t0
        logger.info("Ingest PDF done: %s -> %d new chunks (%.2fs)", fname, len(docs), dt)
        return {"ok": True, "chunks": len(docs), "file": fname, "seconds": round(dt, 2)}
    except Exception as e:
        logger.exception("Ingest PDF failed: %s", fname)
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@app.post("/ingest/folder")
def ingest_folder(path: str = Form(...)):
    """
    Quick folder ingest: reads all PDFs under 'path' on server.
    *Use only if the PDFs exist on the server filesystem.*
    """
    import glob
    import pathlib

    t0 = time.time()
    pdfs = glob.glob(str(pathlib.Path(path) / "**/*.pdf"), recursive=True)
    logger.info("Folder ingest start: %s -> %d PDFs", path, len(pdfs))

    total_chunks = 0
    files_done = 0
    for pdf_path in pdfs:
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            fname = os.path.basename(pdf_path)
            chunks = _pdf_to_texts(pdf_bytes, fname)
            if not chunks:
                logger.warning("No extractable text: %s", fname)
                continue
            ids = []
            docs = []
            metas = []
            for c in chunks:
                if not _is_duplicate_chunk(c["text"], c["metadata"]):
                    ids.append(c["id"])
                    docs.append(c["text"])
                    metas.append(c["metadata"])
            if not docs:
                logger.info("All chunks for %s are duplicates, skipping.", fname)
                continue
            vecs = _embed(docs)
            coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)
            total_chunks += len(docs)
            files_done += 1
            logger.info("Ingested %s -> %d new chunks", fname, len(docs))
        except Exception as e:
            logger.exception("Failed ingest for %s", pdf_path)

    dt = time.time() - t0
    logger.info("Folder ingest done: %d/%d files, %d chunks (%.2fs)", files_done, len(pdfs), total_chunks, dt)
    return {"ok": True, "chunks": total_chunks, "files": files_done, "seconds": round(dt, 2)}

@app.get("/stats")
def stats():
    try:
        cnt = coll.count()
    except Exception:
        cnt = -1
    return {"collection": COLLECTION_NAME, "count": cnt, "persist_directory": CHROMA_DIR}


# ---------- Retrieval + Answer ----------
SYSTEM_PROMPT = (
    "You are a careful assistant answering only from provided context about flower medicine "
    "and related material. If the answer is not in the context, say you don't know. "
    "Never provide diagnosis or treatment. Include concise citations like [1], [2] "
    "that map to sources. If health/contraindications appear, add a one-line disclaimer."
)

def _build_prompt(question: str, contexts: List[Dict[str, Any]]) -> str:
    numbered_sections = []
    for i, c in enumerate(contexts, start=1):
        meta = c.get("metadata", {})
        src = meta.get("source", "unknown")
        page = meta.get("page", None)
        where = f"{src}" + (f", p.{page}" if page else "")
        numbered_sections.append(f"[{i}] {c['text']}\n(Source: {where})")
    ctx = "\\n\\n".join(numbered_sections)
    return (
        f"Answer the question using ONLY the context.\\n\\n"
        f"Question: {question}\\n\\n"
        f"Context:\\n{ctx}\\n\\n"
        f"Instructions:\\n"
        f"- Cite passages with [n] where n corresponds to the sources list above.\\n"
        f"- If uncertain, say you don't know from these documents.\\n"
        f"- Add a one-line disclaimer if health/contraindications are discussed.\\n\\n"
        f"Answer:\\n"
    )

@app.post("/ask", response_model=AskOut)
def ask(payload: AskIn):
    k = payload.k or TOP_K
    qvec = _embed([payload.question])[0]
    res = coll.query(query_embeddings=[qvec], n_results=k, where=payload.where or None)
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]

    contexts = [{"text": d, "metadata": m} for d, m in zip(docs, metas)]
    if not contexts:
        return AskOut(answer="I couldn't find anything in the current index.", citations=[])

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


# ---------- Root: serve the barebones UI ----------
@app.get("/", response_class=HTMLResponse)
def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ---------- Admin route: serve the ingest UI ----------
@app.get("/admin", response_class=HTMLResponse)
def admin():
    with open("static/admin.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
