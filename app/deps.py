from fastapi import Depends
from openai import OpenAI
from .config import OPENAI_CHAT_MODEL
from .chroma import coll
from app.services.planner import Planner
from app.services.recommender import Recommender
from app.services.retriever import Retriever
from app.services.logger import LoggerService
def get_logger():
    return LoggerService()

def get_oa():
    return OpenAI()

def get_retriever():
    return Retriever(coll)

def get_planner(oa=Depends(get_oa)):
    return Planner(oa, OPENAI_CHAT_MODEL)

def get_recommender(oa=Depends(get_oa), retriever=Depends(get_retriever)):
    return Recommender(oa, OPENAI_CHAT_MODEL, retriever)
