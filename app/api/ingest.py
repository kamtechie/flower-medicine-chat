import glob
import os
import pathlib
import time
from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from app.core.logging import get_logger
from app.core.deps import get_ingest_service
from app.services.ingest import IngestService, IngestResult

router = APIRouter()

@router.post("/ingest/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    logger = Depends(lambda: get_logger(__name__)),
    ingest_service: IngestService = Depends(get_ingest_service)
):
    fname = file.filename
    if not fname:
        return JSONResponse({"ok": False, "msg": "Filename is required."}, status_code=400)
    if not fname.lower().endswith(".pdf"):
        return JSONResponse({"ok": False, "msg": "Only PDF files are supported."}, status_code=400)
    try:
        data = await file.read()
        result: IngestResult = ingest_service.ingest_document(data, fname)
        if result.error:
            return JSONResponse({"ok": False, "msg": result.error}, status_code=result.status)
        return {"ok": True, "chunks": result.count, "file": fname, "seconds": round(result.seconds or 0, 2)}
    except Exception as e:
        logger.exception("ingest.pdf.failed", filename=fname, error=str(e))
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)

@router.post("/ingest/folder")
def ingest_folder(
    path: str = Form(...),
    logger = Depends(lambda: get_logger(__name__)),
    ingest_service: IngestService = Depends(get_ingest_service)
):
    try:
        result: IngestResult = ingest_service.ingest_folder(path)
        if result.error:
            return JSONResponse({"ok": False, "msg": result.error}, status_code=result.status)
        return {"ok": True, "chunks": result.count, "files": None, "seconds": round(result.seconds or 0, 2)}
    except Exception as e:
        logger.exception("ingest.folder.failed", path=path, error=str(e))
        return JSONResponse({"ok": False, "msg": str(e)}, status_code=500)
