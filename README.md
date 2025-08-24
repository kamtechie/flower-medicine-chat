# Flower Medicine Q&A

A minimal chatbot that answers questions from your PDF books using **ChromaDB** and **OpenAI**.

---

## Run Locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# set your API key
export OPENAI_API_KEY=sk-...

# start the server
uvicorn app:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

---

## Run with Docker

```bash
docker build -t flower-rag .
docker run -it --rm -p 8000:8000   -e OPENAI_API_KEY=sk-...   -e CHROMA_DIR=/data/chroma   -v $(pwd)/chroma:/data/chroma   flower-rag
```

---

## Ingest PDFs

### Upload via Web UI
Go to [http://127.0.0.1:8000](http://127.0.0.1:8000) and use the **Upload a PDF** form.

### Ingest via API
Single PDF:
```bash
curl -F "file=@/path/to/book.pdf" http://127.0.0.1:8000/ingest/pdf
```

Folder of PDFs (server-side path):
```bash
curl -F "path=/absolute/path/to/pdfs" http://127.0.0.1:8000/ingest/folder
```
