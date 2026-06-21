from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, backtests, dashboard, funds, jobs, market, portfolio, prices, reports, review, settings as settings_api, signals, stocks, strategies, watchlist
from app.core.config import get_settings


settings = get_settings()

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(stocks.router, prefix="/api")
app.include_router(funds.router, prefix="/api")
app.include_router(prices.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(backtests.router, prefix="/api")
app.include_router(signals.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(settings_api.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/health/cors")
def cors_health() -> dict:
    return {
        "status": "ok",
        "frontend_public_url": settings.frontend_public_url,
        "cors_origins": settings.cors_origins,
        "cors_origin_regex": settings.cors_origin_regex,
    }

