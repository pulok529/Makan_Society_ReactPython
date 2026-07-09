import logging
import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.accounting.router import router as accounting_router
from app.modules.billing.router import router as billing_router
from app.modules.categories.router import router as categories_router
from app.modules.jobs.router import router as jobs_router
from app.modules.members.router import router as members_router
from app.modules.messaging.router import router as messaging_router, sms_router
from app.modules.packages.router import router as packages_router
from app.modules.reporting.router import router as reporting_router
from app.modules.system.router import router as system_router

logger = logging.getLogger("app.performance")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def slow_request_logger(request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000
        if duration_ms >= 1000:
            logger.warning(
                "slow_request path=%s method=%s status=%s duration_ms=%.2f",
                request.url.path,
                request.method,
                response.status_code,
                duration_ms,
            )
        return response

    app.include_router(system_router)
    app.include_router(auth_router, prefix="/api")
    app.include_router(accounting_router, prefix="/api")
    app.include_router(billing_router, prefix="/api")
    app.include_router(categories_router, prefix="/api")
    app.include_router(jobs_router, prefix="/api")
    app.include_router(packages_router, prefix="/api")
    app.include_router(members_router, prefix="/api")
    app.include_router(messaging_router, prefix="/api")
    app.include_router(sms_router, prefix="/api")
    app.include_router(reporting_router, prefix="/api")
    return app


app = create_app()
