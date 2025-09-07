from app.core.settings import settings
from app.services.chroma import ChromaService


class ChromaRepository:
    def __init__(
        self, chroma_service: ChromaService, collection_name: str = settings.COLLECTION_NAME
    ):
        self.client = chroma_service.get_client()
        self.collection = self.client.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

    def upsert(self, **kwargs):
        return self.collection.upsert(**kwargs)

    def query(self, **kwargs):
        return self.collection.query(**kwargs)
