from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-5-nano"
    CHROMA_DIR: str = "./chroma"
    COLLECTION_NAME: str = "flower_medicine"
    TOP_K: int = 8
    CHUNK_CHARS: int = 1800
    CHUNK_OVERLAP: int = 250
    OPENAI_API_KEY: str = ""
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env"
    }

settings = Settings()