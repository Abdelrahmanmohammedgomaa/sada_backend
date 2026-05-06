from fastapi import FastAPI
from app.database import engine, Base
from app.routes import auth
from app.models import parent, child # تأكد إنك ضفت child هنا

# كارييت الجداول
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SADA Backend")

# ربط الروتس
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to SADA API"}


from app.database import engine, Base
