from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from app.database import engine, Base
from app.routes import auth, parents
# from app.routes import exercises  # TODO: Create Exercise and Progress models
from app.models import parent, child

# Ensure folder for audio uploads
UPLOADS_AUDIO_PATH = 'uploads/audio'
os.makedirs(UPLOADS_AUDIO_PATH, exist_ok=True)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SADA Backend")

# Register routers
app.include_router(auth.router)
# app.include_router(exercises.router)  # TODO: Uncomment when Exercise model is created
app.include_router(parents.router)

# Serve uploads folder as static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to SADA API"}
