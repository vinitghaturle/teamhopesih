"""Tender Guard — AI Recommender of Indian Standards for Procurement Tenders.

FastAPI Backend Application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers.analyze import router as analyze_router
from routers.standards import router as standards_router
from routers.review import router as review_router
from routers.portal import router as portal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    print("=" * 60)
    print("  Tender Guard Backend -- Initializing...")
    print("=" * 60)
    init_db()
    print("[Startup] SQLite database verified.")
    print("=" * 60)
    print("  Tender Guard API Ready")
    print("=" * 60)
    yield
    print("[Shutdown] Tender Guard Backend shutting down.")


app = FastAPI(
    title="Tender Guard API",
    description="AI Recommender of Bureau of Indian Standards (BIS) for Procurement Tenders.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(analyze_router)
app.include_router(standards_router)
app.include_router(review_router)
app.include_router(portal_router)


@app.get("/", tags=["system"])
def root():
    return {
        "service": "Tender Guard API",
        "version": "1.0.0",
        "status": "online",
        "frontend_ui": "http://localhost:3000",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/api/health",
        "message": "Welcome to Tender Guard API. Visit http://localhost:3000 for the Web UI or /docs for API documentation."
    }


@app.get("/api/health", tags=["system"])
def health_check():
    from database import SessionLocal
    from models.schema import Standard
    from services.pipeline_service import get_shared_retrieval_pipeline

    db = SessionLocal()
    std_count = 0
    try:
        std_count = db.query(Standard).count()
    except Exception:
        pass
    finally:
        db.close()

    pipeline = get_shared_retrieval_pipeline()
    neural_ready = getattr(pipeline, "neural_available", False)

    return {
        "status": "healthy",
        "service": "Tender Guard API",
        "version": "1.0.0",
        "database": {
            "status": "connected",
            "standards_count": std_count,
        },
        "models": {
            "bi_encoder": "BAAI/bge-small-en-v1.5",
            "cross_encoder": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "neural_ready": neural_ready,
            "degraded_bm25_only": not neural_ready,
        },
        "multilingual": {
            "languages_supported": ["en", "hi", "mr"],
            "glossary_terms": "150+ terms",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
