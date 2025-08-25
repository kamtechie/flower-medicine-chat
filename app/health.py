from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .chroma import coll
from .config import COLLECTION_NAME, CHROMA_DIR

router = APIRouter()

@router.get("/stats")
def stats():
    try:
        cnt = coll.count()
    except Exception:
        cnt = -1
    return {"collection": COLLECTION_NAME, "count": cnt, "persist_directory": CHROMA_DIR}

@router.get("/health")
def health():
    return {"status": "ok"}
