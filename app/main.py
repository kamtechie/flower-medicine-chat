from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .ingest import router as ingest_router
from .retrieval import router as retrieval_router
from .health import router as health_router

app = FastAPI(title="Flower Medicine RAG (Chroma + FastAPI)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="static/preact/assets"), name="assets")

app.include_router(ingest_router)
app.include_router(retrieval_router)
app.include_router(health_router)

@app.get("/", response_class=HTMLResponse)
def root():
    with open("static/preact/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/admin", response_class=HTMLResponse)
def admin():
    with open("static/preact/index.html", "r", encoding="utf-8") as f:
        return f.read()
