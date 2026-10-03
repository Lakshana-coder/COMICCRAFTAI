from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.create_directories()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered comic story creator using "
        "Gemini and image generation."
    ),
    lifespan=lifespan,
)



app.mount(
    "/static",
    StaticFiles(
        directory=str(settings.STATIC_DIR)
    ),
    name="static",
)


templates = Jinja2Templates(
    directory=str(settings.TEMPLATE_DIR)
)

app.state.templates = templates

app.include_router(router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }