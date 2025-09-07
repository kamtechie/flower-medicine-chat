from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from asgi_correlation_id import CorrelationIdMiddleware
from app.core.logging import setup_logging
from app.core.bind_context import BindSessionMiddleware
from app.api.ingest import router as ingest_router
from app.api.retrieval import router as retrieval_router
from app.api.health import router as health_router
from app.api.dialog import router as dialog_router

setup_logging()
app = FastAPI(title="Zenji RAG (Chroma + FastAPI)")
app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.add_middleware(BindSessionMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

app.include_router(ingest_router, prefix="/api")
app.include_router(retrieval_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(dialog_router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/ingest", response_class=HTMLResponse)
def admin():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
