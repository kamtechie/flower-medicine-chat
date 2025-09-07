from fastapi import HTTPException

from app.services.openai import OpenAIService
from app.repositories.chroma import ChromaRepository

class Retriever:
    def __init__(self, oa: OpenAIService, chroma_repo: ChromaRepository):
        self.openai = oa
        self.chroma_repo = chroma_repo

    def retrieve(self, summary: str, k: int = 12):
        qvecs = self.openai.embed([summary])
        if not qvecs:
            raise HTTPException(status_code=500, detail="Failed to embed question.")
        qvec = qvecs[0]
        res = self.chroma_repo.query(query_embeddings=[qvec], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"text": d, "meta": m} for d, m in zip(docs, metas)]
