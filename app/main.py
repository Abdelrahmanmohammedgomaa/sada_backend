from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routes import auth, exercises
from app.models import parent, child, exercise, progress  # <-- Make sure these are imported

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SADA Backend")

# Register routers
app.include_router(auth.router)
app.include_router(exercises.router)

# Serve uploads folder as static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "Welcome to SADA API"}
