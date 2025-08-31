from fastapi import HTTPException

from app.services.openai import OpenAIService

class Retriever:
    def __init__(self, oa: OpenAIService, coll):
        self.openai = oa
        self.coll = coll

    def retrieve(self, summary: str, k: int = 12):
        # res = self.coll.query(query_texts=[summary], n_results=k)
        qvecs = self.openai.embed([summary])
        if not qvecs:
            raise HTTPException(status_code=400, detail="Failed to embed question.")
        qvec = qvecs[0]
        res = self.coll.query(query_embeddings=[qvec], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"text": d, "meta": m} for d, m in zip(docs, metas)]
