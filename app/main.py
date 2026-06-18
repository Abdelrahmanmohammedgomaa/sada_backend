from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine, Base
from app.routes import auth, parents, exercises
from app.models import parent, child, exercise, progress

# Ensure folder for audio uploads
UPLOADS_AUDIO_PATH = 'uploads/audio'
UPLOADS_IMAGE_PATH = "uploads/images"
os.makedirs(UPLOADS_AUDIO_PATH, exist_ok=True)
os.makedirs(UPLOADS_IMAGE_PATH, exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SADA Backend")

# ============================================================================
# CORS Configuration
# ============================================================================
# CORS (Cross-Origin Resource Sharing) is required to allow frontend applications
# running on different domains/machines to communicate with this API.
# This is essential for:
#   - Development: Frontend (localhost:3000) accessing API (localhost:8000)
#   - Production: Frontend domain accessing API domain from different origins
# Without CORS configuration, browsers will block API requests with CORS errors.
#
# Environment-aware configuration:
#   - DEVELOPMENT: Allow all origins (wildcard "*") for maximum flexibility
#   - PRODUCTION: Should be restricted to specific frontend domains
#
# Frontend teams should set CORS_ORIGINS env var in production like:
#   CORS_ORIGINS="https://frontend.example.com,https://app.example.com"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")  # Default to "*" for development

# Parse CORS_ORIGINS: if it's not "*", split by comma and strip whitespace
if CORS_ORIGINS == "*":
    allowed_origins = ["*"]
else:
    allowed_origins = [origin.strip() for origin in CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # List of allowed origins
    allow_credentials=False if "*" in allowed_origins else True,
    # Note: When allow_origins=["*"], allow_credentials must be False
    # This is a browser security requirement
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, PATCH, OPTIONS, etc.)
    allow_headers=["*"],  # Allow all headers (Authorization, Content-Type, etc.)
)

# Register routers
app.include_router(auth.router)
app.include_router(exercises.router)
app.include_router(parents.router)

# Serve uploads folder as static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to SADA API"}
