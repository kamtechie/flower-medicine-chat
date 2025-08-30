from fastapi import APIRouter
from fastapi.responses import JSONResponse
from .chroma import coll
from app.settings import settings
from fastapi import Depends

router = APIRouter()

@router.get("/stats")
def stats(settings=Depends(lambda: settings)):
    try:
        cnt = coll.count()
    except Exception:
        cnt = -1
    return {"collection": settings.COLLECTION_NAME, "count": cnt, "persist_directory": settings.CHROMA_DIR}

@router.get("/health")
def health(settings=Depends(lambda: settings)):
    return {"status": "ok"}
