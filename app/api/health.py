from fastapi import APIRouter, Depends
from app.core.settings import settings
from app.core.deps import get_chroma_repository
from app.repositories.chroma import ChromaRepository

router = APIRouter()

@router.get("/stats")
def stats(settings=Depends(lambda: settings), chroma_repo: ChromaRepository = Depends(get_chroma_repository)):
    try:
        cnt = chroma_repo.collection.count()
    except Exception:
        cnt = -1
    return {"collection": settings.COLLECTION_NAME, "count": cnt, "persist_directory": settings.CHROMA_DIR}

@router.get("/health")
def health():
    return {"status": "ok"}
