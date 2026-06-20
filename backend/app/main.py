from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, jobs, market, portfolio, stocks, watchlist
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}

