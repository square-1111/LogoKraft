from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv

from app.routes import stream_routes, auth_routes, project_routes
from app.models.schemas import HealthResponse
from app.services.supabase_service import supabase_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LogoKraft API",
    description="AI-powered logo generation backend with authentication and project management",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_routes.router)
app.include_router(project_routes.router)
app.include_router(stream_routes.router)  # Keep legacy test endpoint

@app.get("/", 
    summary="API Root", 
    description="Basic API information and status"
)
async def root():
    return {
        "message": "LogoKraft API is running",
        "version": "0.2.0",
        "milestone": "3-ai-integration",
        "docs": "/api/docs"
    }

@app.get("/health", 
    response_model=HealthResponse,
    summary="Health Check",
    description="Check API and database health status"
)
async def health_check():
    """
    Comprehensive health check for API and dependencies.
    """
    try:
        # Check database connection
        db_healthy = await supabase_service.health_check()
        
        return HealthResponse(
            status="healthy" if db_healthy else "degraded",
            services={
                "api": True,
                "database": db_healthy,
                "supabase": db_healthy
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            services={
                "api": True,
                "database": False,
                "supabase": False
            }
        )