from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import stream_routes

load_dotenv()

app = FastAPI(
    title="LogoKraft API",
    description="AI-powered logo generation backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stream_routes.router)

@app.get("/")
async def root():
    return {"message": "LogoKraft API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "milestone": "1-smoke-test"}