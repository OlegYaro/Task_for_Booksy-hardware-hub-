import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed the database on startup.
    Base.metadata.create_all(bind=engine)
    from app.seed import seed_database

    seed_database()
    yield


app = FastAPI(title="Hardware Hub API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


def register_routers():
    from app.routers import ai, auth, hardware, rentals

    app.include_router(auth.router)
    app.include_router(hardware.router)
    app.include_router(rentals.router)
    app.include_router(ai.router)


register_routers()


def _mount_frontend():
    """Serve the built Vue SPA from the backend when a build is present.

    In production we ship one service: FastAPI answers `/api/*` and serves the
    Vite build for everything else, so there's a single origin and no CORS. In
    local dev the build usually isn't there, so this is a no-op and the Vite dev
    server proxies `/api` instead. STATIC_DIR lets the container point at the
    copied build; otherwise we look for frontend/dist next to the repo.
    """
    env_dir = os.environ.get("STATIC_DIR")
    static_dir = (
        Path(env_dir)
        if env_dir
        else Path(__file__).resolve().parents[2] / "frontend" / "dist"
    )
    index = static_dir / "index.html"
    if not index.is_file():
        return

    assets = static_dir / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    # Catch-all: real files (favicon, etc.) are served as-is; every other path
    # falls back to index.html so client-side routes survive a hard refresh.
    # Registered last, so it never shadows /api/* or the docs.
    @app.get("/{full_path:path}")
    def spa(full_path: str):
        candidate = static_dir / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


_mount_frontend()
