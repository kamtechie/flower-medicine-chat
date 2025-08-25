import os
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pypdf import PdfReader
from io import BytesIO
from .utils import _chunk_text
from .chroma import coll
from .config import logger

router = APIRouter()

def _pdf_to_texts(pdf_bytes: bytes, filename: str):
    reader = PdfReader(BytesIO(pdf_bytes))
    items = []
    for p, page in enumerate(reader.pages, start=1):
        try:
            txt = page.extract_text() or ""
        except Exception as e:
            logger.warning("PDF text extraction error on %s page %d: %s", filename, p, e)
            txt = ""
        if txt.strip():
            items.extend(_chunk_text(txt, {"source": filename, "page": p}))
    return items

@router.post("/ingest/pdf")
async def ingest_pdf(file: UploadFile = File(...)):
    import time
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
        from .utils import _get_token_count
        from openai import OpenAI
        oa = OpenAI()
        def _embed(texts):
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
                resp = oa.embeddings.create(model="text-embedding-3-small", input=batch)
                out.extend([d.embedding for d in resp.data])
            return out

        embeddings = _embed([c["text"] for c in chunks])
        def _is_duplicate_chunk(chunk_embedding, chunk_text, source_meta):
            results = coll.query(query_embeddings=[chunk_embedding], where={"source": source_meta.get("source")}, n_results=1)
            docs = results.get("documents", [[]])[0]
            return any(doc == chunk_text for doc in docs)

        for c, emb in zip(chunks, embeddings):
            if not _is_duplicate_chunk(emb, c["text"], c["metadata"]):
                ids.append(c["id"])
                docs.append(c["text"])
                metas.append(c["metadata"])
        if not docs:
            logger.info("All chunks for %s are duplicates, skipping.", fname)
            return JSONResponse({"ok": False, "msg": "All chunks are duplicates."}, status_code=200)
        vecs = [emb for c, emb in zip(chunks, embeddings) if not _is_duplicate_chunk(emb, c["text"], c["metadata"])]
        coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)

        dt = time.time() - t0
        logger.info("Ingest PDF done: %s -> %d new chunks (%.2fs)", fname, len(docs), dt)
        return {"ok": True, "chunks": len(docs), "file": fname, "seconds": round(dt, 2)}
    except Exception as e:
        logger.exception("Ingest PDF failed: %s", fname)
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@router.post("/ingest/folder")
def ingest_folder(path: str = Form(...)):
    import glob
    import pathlib
    import time
    t0 = time.time()
    pdfs = glob.glob(str(pathlib.Path(path) / "**/*.pdf"), recursive=True)
    logger.info("Folder ingest start: %s -> %d PDFs", path, len(pdfs))

    total_chunks = 0
    files_done = 0
    from .utils import _get_token_count
    from openai import OpenAI
    oa = OpenAI()
    def _embed(texts):
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
            resp = oa.embeddings.create(model="text-embedding-3-small", input=batch)
            out.extend([d.embedding for d in resp.data])
        return out

    def _is_duplicate_chunk(chunk_embedding, chunk_text, source_meta):
        results = coll.query(query_embeddings=[chunk_embedding], where={"source": source_meta.get("source")}, n_results=1)
        docs = results.get("documents", [[]])[0]
        return any(doc == chunk_text for doc in docs)

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
            embeddings = _embed([c["text"] for c in chunks])
            for c, emb in zip(chunks, embeddings):
                if not _is_duplicate_chunk(emb, c["text"], c["metadata"]):
                    ids.append(c["id"])
                    docs.append(c["text"])
                    metas.append(c["metadata"])
            if not docs:
                logger.info("All chunks for %s are duplicates, skipping.", fname)
                continue
            vecs = [emb for c, emb in zip(chunks, embeddings) if not _is_duplicate_chunk(emb, c["text"], c["metadata"])]
            coll.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)
            total_chunks += len(docs)
            files_done += 1
            logger.info("Ingested %s -> %d new chunks", fname, len(docs))
        except Exception as e:
            logger.exception("Failed ingest for %s", pdf_path)

    dt = time.time() - t0
    logger.info("Folder ingest done: %d/%d files, %d chunks (%.2fs)", files_done, len(pdfs), total_chunks, dt)
    return {"ok": True, "chunks": total_chunks, "files": files_done, "seconds": round(dt, 2)}
