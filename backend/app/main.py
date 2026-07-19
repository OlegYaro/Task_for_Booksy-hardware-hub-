from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
