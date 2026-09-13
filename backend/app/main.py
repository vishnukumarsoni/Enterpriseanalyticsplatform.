import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.database import check_db_connection
from app.routes import dashboard, sales, customers, products, regions, employees, churn, rfm, forecast, insights, data_quality

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("main")

settings = get_settings()

app = FastAPI(
    title="Enterprise Sales, Customer & Revenue Analytics Platform API",
    description="Backend API for the Enterprise Analytics Hub — sales, customer, product, "
                "regional, churn, RFM, and forecasting analytics.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 1)
    log.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response


@app.exception_handler(ValidationError)
async def pydantic_validation_handler(request: Request, exc: ValidationError):
    log.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": [
            {"loc": e.get("loc"), "msg": e.get("msg"), "type": e.get("type")}
            for e in exc.errors()
        ]},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )


@app.get("/api/health", tags=["health"])
def health_check():
    db_ok = check_db_connection()
    return {"status": "ok" if db_ok else "degraded", "database_connected": db_ok}


app.include_router(dashboard.router)
app.include_router(sales.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(regions.router)
app.include_router(employees.router)
app.include_router(churn.router)
app.include_router(rfm.router)
app.include_router(forecast.router)
app.include_router(insights.router)
app.include_router(data_quality.router)
