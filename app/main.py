import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.loads import load_loads_from_csv
from app.routes import calls, carriers, health, loads as loads_routes, metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())
    logging.getLogger(__name__).info("Starting up — initializing DB and loading loads CSV")
    init_db()
    load_loads_from_csv()
    yield
    logging.getLogger(__name__).info("Shutting down")


app = FastAPI(
    title="HappyRobot Carrier Sales API",
    version="0.1.0",
    lifespan=lifespan,
    description="Backend for inbound carrier load sales automation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(carriers.router)
app.include_router(loads_routes.router)
app.include_router(calls.router)
app.include_router(metrics.router)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def dashboard_root():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Dashboard coming soon"}
