"""FastAPI application entrypoint for VeilPass API."""

from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from structlog import get_logger

from app.config import settings
from app.errors import VeilPassError, veilpass_exception_handler, unhandled_exception_handler
from app.routes import health, qr, nfc, links, urls, tokens, verify, api_keys

logger = get_logger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup / shutdown lifecycle."""
    logger.info(
        "veilpass_api_started",
        app_name=settings.app_name,
        version=settings.version,
        debug=settings.debug,
    )
    yield
    logger.info("veilpass_api_shutdown")


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Ensure every request has a request ID."""
    from app.deps import request_id_dependency

    await request_id_dependency(request)
    response = await call_next(request)
    request_id = getattr(request.state, "request_id", "")
    response.headers["X-Request-ID"] = request_id
    return response


# ── Exception handlers ────────────────────────────────────────────────────────

app.add_exception_handler(VeilPassError, veilpass_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Static files mount ─────────────────────────────────────────────────────────

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")
else:
    logger.info("static_directory_not_found", path=_static_dir)

# ── Routers ────────────────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(qr.router)
app.include_router(nfc.router)
app.include_router(links.router)
app.include_router(urls.router)
app.include_router(tokens.router)
app.include_router(verify.router)
app.include_router(api_keys.router)
