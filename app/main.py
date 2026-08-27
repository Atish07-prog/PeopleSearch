from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes.health import router as health_router
from app.api.routes.search import router as search_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, version="0.1.0")
_frontend_path = Path(__file__).parent / "static" / "index.html"
app.include_router(health_router)
app.include_router(search_router)


@app.get("/", response_class=HTMLResponse)
def frontend() -> HTMLResponse:
    return HTMLResponse(_frontend_path.read_text(encoding="utf-8"))
