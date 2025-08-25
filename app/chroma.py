from chromadb import PersistentClient
from .config import CHROMA_DIR, COLLECTION_NAME, logger

chroma = PersistentClient(path=CHROMA_DIR)
logger.info("Chroma persistence directory: %s", CHROMA_DIR)
coll = chroma.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)
