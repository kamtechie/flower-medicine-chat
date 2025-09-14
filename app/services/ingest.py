from io import BytesIO
from time import time
from dataclasses import dataclass
from typing import Optional, Sequence, Any

from pypdf import PdfReader
from app.core.logging import get_logger
from app.core.utils import _chunk_text, _get_token_count
from app.repositories.chroma import ChromaRepository
from app.services.openai import OpenAIService

@dataclass
class IngestResult:
    count: int
    error: Optional[str]
    status: int
    seconds: Optional[float]

class IngestService:
    def __init__(self, chroma_repo: ChromaRepository, openai_service: OpenAIService):
        self.logger = get_logger(__name__)
        self.chroma_repo = chroma_repo
        self.openai_service = openai_service

    def _pdf_to_texts(self, pdf_bytes: bytes, filename: str):
        reader = PdfReader(BytesIO(pdf_bytes))
        items = []
        for p, page in enumerate(reader.pages, start=1):
            try:
                txt = page.extract_text() or ""
            except Exception as e:
                self.logger.warning("pdf.extract.error", filename=filename, page=p, error=str(e))
                txt = ""
            if txt.strip():
                items.extend(_chunk_text(txt, {"source": filename, "page": p}))
        return items

    def _embed(self, texts):
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
            out.extend(self.openai_service.embed(batch))
        return out
    
    def _is_duplicate_chunk(self, chunk_embedding, chunk_text, source_meta):
        results = self.chroma_repo.query(query_embeddings=[chunk_embedding], where={"source": source_meta.get("source")}, n_results=1)
        docs = results.get("documents", [[]])[0] if results and results.get("documents") else []
        return any(doc == chunk_text for doc in docs)

    def ingest_document(self, data: bytes, fname: str) -> IngestResult:
        t0 = time()
        size_kb = round(len(data) / 1024, 2)
        self.logger.info("ingest.pdf.start", filename=fname, size_kb=size_kb)
        
        chunks = self._pdf_to_texts(data, fname)
        if not chunks:
            self.logger.warning("ingest.pdf.no_text", filename=fname)
            return IngestResult(None, "No extractable text found.", 400, None)

        embeddings = self._embed([c["text"] for c in chunks])

        filtered = [
            (c["id"], c["text"], c["metadata"], emb)
            for c, emb in zip(chunks, embeddings)
            if not self._is_duplicate_chunk(emb, c["text"], c["metadata"])
        ]
        
        if not filtered:
            self.logger.info("ingest.pdf.duplicates", filename=fname)
            return IngestResult(None, "All chunks are duplicates.", 200, None)
        
        ids, docs, metas, vecs = zip(*filtered)
        self.chroma_repo.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)

        dt = time() - t0
        self.logger.info("ingest.pdf.done", filename=fname, chunks=len(docs), seconds=round(dt,2))
        return IngestResult(list(docs), None, 200, dt)

    def ingest_folder(self, path: str) -> IngestResult:
        import glob
        import os
        import pathlib
        t0 = time()
        pdfs = glob.glob(str(pathlib.Path(path) / "**/*.pdf"), recursive=True)
        self.logger.info("ingest.folder.start", path=path, pdf_count=len(pdfs))
        total_chunks = 0
        files_done = 0
        for pdf_path in pdfs:
            try:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                fname = os.path.basename(pdf_path)
                chunks = self._pdf_to_texts(pdf_bytes, fname)
                if not chunks:
                    self.logger.warning("ingest.folder.no_text", filename=fname)
                    continue
                ids = []
                docs = []
                metas = []
                embeddings = self._embed([c["text"] for c in chunks])
                for c, emb in zip(chunks, embeddings):
                    if not self._is_duplicate_chunk(emb, c["text"], c["metadata"]):
                        ids.append(c["id"])
                        docs.append(c["text"])
                        metas.append(c["metadata"])
                if not docs:
                    self.logger.info("ingest.folder.duplicates", filename=fname)
                    continue
                vecs = [emb for c, emb in zip(chunks, embeddings) if not self._is_duplicate_chunk(emb, c["text"], c["metadata"])]
                self.chroma_repo.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=vecs)
                total_chunks += len(docs)
                files_done += 1
                self.logger.info("ingest.folder.file_done", filename=fname, chunks=len(docs))
            except Exception as e:
                self.logger.exception("ingest.folder.failed", filename=pdf_path, error=str(e))
        dt = time() - t0
        self.logger.info("ingest.folder.done", files_done=files_done, total_chunks=total_chunks, seconds=round(dt,2))
        return IngestResult(total_chunks, None, 200, dt)