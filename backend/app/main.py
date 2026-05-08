from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.accounting.router import router as accounting_router
from app.modules.billing.router import router as billing_router
from app.modules.categories.router import router as categories_router
from app.modules.members.router import router as members_router
from app.modules.messaging.router import router as messaging_router, sms_router
from app.modules.packages.router import router as packages_router
from app.modules.reporting.router import router as reporting_router
from app.modules.system.router import router as system_router


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
    app.include_router(system_router)
    app.include_router(auth_router, prefix="/api")
    app.include_router(accounting_router, prefix="/api")
    app.include_router(billing_router, prefix="/api")
    app.include_router(categories_router, prefix="/api")
    app.include_router(packages_router, prefix="/api")
    app.include_router(members_router, prefix="/api")
    app.include_router(messaging_router, prefix="/api")
    app.include_router(sms_router, prefix="/api")
    app.include_router(reporting_router, prefix="/api")
    return app


app = create_app()
