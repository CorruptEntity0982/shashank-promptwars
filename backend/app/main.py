from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routes import patients, documents, health
from app.services.graph_service import graph_service
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Application starting up...")
    logger.info("Ensuring Neo4j constraints are created...")
    try:
        graph_service.ensure_constraints()
        logger.info("Neo4j constraints initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j constraints: {str(e)}")   
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("Application shutting down...")

    try:
        graph_service.close()
        logger.info("Neo4j connection closed")
    except Exception as e:
        logger.error(f"Error closing Neo4j connection: {str(e)}")
    
    logger.info("Application shutdown complete")

app.include_router(health.router)
app.include_router(patients.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    """Hello World endpoint"""
    return {"message": "Hello World from OpenClaims!"}
