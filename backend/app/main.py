# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database.database import engine, Base
from app.models import user, prediction  # Make sure prediction model is imported
from app.routes import auth, predict
from app.routes import auth, predict, users
# Create all tables in the SQLite database (add new models automatically)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriMind Ethiopia API",
    version="1.0.0",
    description="AI-powered agriculture assistant for Ethiopian farmers",
)

# Allow Flutter app (or any frontend) to connect – adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(users.router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
@app.get("/")
def root():
    return {"message": "AgriMind Ethiopia API is running"}

@app.get("/debug/test")
def test():
    from app.utils.security import hash_password
    return {"hash": hash_password("test")}