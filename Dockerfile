# Production Dockerfile for ResilienceAI Platform on Google Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, static assets, and index.html
COPY backend/ ./backend/
COPY src/ ./src/
COPY index.html .
COPY docs/ ./docs/

# Default PORT environment variable provided by Cloud Run
ENV PORT=8080

EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
