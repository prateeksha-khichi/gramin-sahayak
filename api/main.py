"""
FastAPI Main Application
Complete REST API for Gramin Sahayak
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from loguru import logger
import os

from api.routes import loan, fraud, rag
from api.schemas.request_response import HealthResponse
from utils.file_utils import init_project_directories
from database.db_manager import db

# Initialize
init_project_directories()

# Create app
app = FastAPI(
    title="Gramin Sahayak API",
    description="Rural Financial Literacy & Loan Assistant API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(loan.router)
app.include_router(fraud.router)
app.include_router(rag.router)


@app.on_event("startup")
async def startup_event():
    """Run on startup"""
    logger.info("🚀 Starting Gramin Sahayak API")
    logger.info(f"📊 Database: {os.getenv('DATABASE_URL', 'SQLite').split('@')[-1]}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on shutdown"""
    logger.info("👋 Shutting down Gramin Sahayak API")


@app.get("/", response_model=HealthResponse)
async def root():
    """
    Health check endpoint
    """
    from services.rag_service import RAGService
    
    rag_service = RAGService()
    service_status = rag_service.get_service_status()
    
    return HealthResponse(
        status="healthy" if service_status['service_healthy'] else "degraded",
        timestamp=datetime.utcnow(),
        services={
            "rag": service_status['rag_status'],
            "llm": service_status['llm_available'],
            "database": "connected",
            "loan_model": "loaded",
            "fraud_model": "loaded"
        }
    )


@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "ok", "timestamp": datetime.utcnow()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": str(request.url)
        }
    )


# Run with: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )