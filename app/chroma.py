from chromadb import PersistentClient
from app.core.logging import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

chroma = PersistentClient(path=settings.CHROMA_DIR)
logger.info("ChromaDB client initialized", chroma_dir=settings.CHROMA_DIR)
coll = chroma.get_or_create_collection(
    name=settings.COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
