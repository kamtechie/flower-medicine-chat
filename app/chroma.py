from chromadb import PersistentClient
from app.core.settings import settings
from app.services.logger import LoggerService

chroma = PersistentClient(path=settings.CHROMA_DIR)
LoggerService().info(f"Chroma persistence directory: {settings.CHROMA_DIR}")
coll = chroma.get_or_create_collection(
    name=settings.COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
