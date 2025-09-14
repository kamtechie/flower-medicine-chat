from fastapi import Depends, Request
from app.services.openai import OpenAIService
from app.core.settings import settings
from app.services.planner import Planner
from app.services.recommender import Recommender
from app.services.retriever import Retriever
from app.core.logging import get_logger as _get
from app.services.chroma import ChromaService
from app.repositories.chroma import ChromaRepository
from app.services.ingest import IngestService

def get_logger(name: str = "app"):
    return _get(name)

def get_chroma_service(request: Request) -> ChromaService:
    return request.app.state.chroma_service

def get_chroma_repository(
    chroma_service: ChromaService = Depends(get_chroma_service)
) -> ChromaRepository:
    return ChromaRepository(chroma_service)

def get_openai_service():
    return OpenAIService(settings.OPENAI_API_KEY)

def get_retriever(openai_service=Depends(get_openai_service), chroma_repository=Depends(get_chroma_repository)):
    return Retriever(openai_service, chroma_repository)

def get_planner(openai_service=Depends(get_openai_service)):
    return Planner(openai_service, settings.OPENAI_CHAT_MODEL)

def get_recommender(openai_service=Depends(get_openai_service), retriever=Depends(get_retriever)):
    return Recommender(openai_service, settings.OPENAI_CHAT_MODEL, retriever)

def get_ingest_service(
    chroma_repo: ChromaRepository = Depends(get_chroma_repository),
    openai_service: OpenAIService = Depends(get_openai_service),
) -> IngestService:
    return IngestService(chroma_repo, openai_service)

