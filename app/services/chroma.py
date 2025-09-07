from chromadb import PersistentClient
from chromadb.config import Settings as ChromaSettings
from app.core.settings import settings
from app.core.logging import get_logger


class ChromaService:
    def __init__(self, persist_directory: str | None = None):
        self.logger = get_logger(__name__)
        self.client = PersistentClient(
            path=persist_directory or settings.CHROMA_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.logger.info(
            "chroma.client.initialized", path=persist_directory or settings.CHROMA_DIR
        )

    def get_client(self):
        return self.client
