from fastapi import Depends
from app.services.openai import OpenAIService
from app.core.settings import settings
from app.chroma import coll
from app.services.planner import Planner
from app.services.recommender import Recommender
from app.services.retriever import Retriever
from app.core.logging import get_logger as _get

def get_logger(name: str = "app"):
    return _get(name)

def get_openai_service():
    return OpenAIService(settings.OPENAI_API_KEY)

def get_retriever(openai_service=Depends(get_openai_service)):
    return Retriever(openai_service, coll)

def get_planner(openai_service=Depends(get_openai_service)):
    return Planner(openai_service, settings.OPENAI_CHAT_MODEL)

def get_recommender(openai_service=Depends(get_openai_service), retriever=Depends(get_retriever)):
    return Recommender(openai_service, settings.OPENAI_CHAT_MODEL, retriever)
