# syntax=docker/dockerfile:1

# ---- Stage 1: build the Vue frontend ----
FROM node:20-slim AS frontend
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build          # -> /web/dist

# ---- Stage 2: python backend that also serves the built SPA ----
FROM python:3.14-slim AS app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

COPY backend/ ./
# Drop the built frontend in next to the backend and point the app at it.
COPY --from=frontend /web/dist ./frontend_dist
ENV STATIC_DIR=/app/frontend_dist

# The platform injects $PORT; default to 8000 for a plain `docker run`.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
