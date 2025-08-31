# ---- Frontend build stage ----
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend ./
RUN npm run build

# ---- Python backend stage ----
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App files
COPY app ./app
RUN mkdir -p /app/static

# Copy built frontend from previous stage
COPY --from=frontend-build /app/static ./static

# Chroma persistence directory
RUN mkdir -p /app/chroma
VOLUME ["/app/chroma"]
ENV CHROMA_DIR=/app/chroma

# Healthcheck (simple)
HEALTHCHECK CMD curl --fail http://localhost:8000/api/stats || exit 1

# Optional: Use a non-root user for security
# RUN useradd -m appuser && chown -R appuser /app
# USER appuser

# Run
EXPOSE 8000
ENV PORT=8000
ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]