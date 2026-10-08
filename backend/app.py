"""
ADHAV AI - Stage 6: the web server, the chat page and the memory database.

Run from the project root folder (adhav-ai) with:
    python -m uvicorn backend.app:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend import config, database
from backend.routes import chat
from backend.routes import memory as memory_routes

FRONTEND_DIR = config.PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once when the server starts: make sure the database tables exist."""
    database.init_db()
    yield


app = FastAPI(title="ADHAV AI", version="0.6.0", lifespan=lifespan)

# Plug in the endpoints.
app.include_router(chat.router)
app.include_router(memory_routes.router)
@app.exception_handler(Exception)
async def show_errors(request, exc):
    """Show the real error in the chat instead of a vague message."""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {type(exc).__name__}: {exc}"},
    )

# Serve style.css, app.js and memory.js from the frontend folder at /static/...
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def home():
    """The main address shows the chat page."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(
        status_code=404,
        content={"detail": "frontend/index.html was not found. Check the frontend folder."},
    )


@app.get("/health")
def health():
    """Check that the server is alive and the key is set (never shows the key)."""
    return {
        "status": "ok",
        "app": "ADHAV AI",
        "model": config.GEMINI_MODEL,
        "api_key_set": not config.api_key_is_missing(),
    }
from fastapi import Response

@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    """The browser asks for a tab icon. We have none, so reply 'no content'."""
    return Response(status_code=204)