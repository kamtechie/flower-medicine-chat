class Retriever:
    def __init__(self, coll):
        self.coll = coll

    def retrieve(self, summary: str, k: int = 12):
        res = self.coll.query(query_texts=[summary], n_results=k)
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        return [{"text": d, "meta": m} for d, m in zip(docs, metas)]
