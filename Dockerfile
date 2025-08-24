# ---- Build image ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency list first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files
COPY app.py ./app.py
COPY static ./static

# Chroma persistence directory
RUN mkdir -p /app/chroma
VOLUME ["/app/chroma"]

EXPOSE 8000

# Healthcheck (simple)
HEALTHCHECK CMD curl --fail http://localhost:8000/stats || exit 1

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
