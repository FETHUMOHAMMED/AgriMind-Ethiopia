from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database.database import engine, Base
from app.models import user, prediction, feedback   # feedback added
from app.routes import auth, predict, users, feedback, language

# Create all tables (adds feedbacks table if missing)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AgriMind Ethiopia API",
    version="1.0.0",
    description="AI-powered agriculture assistant for Ethiopian farmers",
)

# Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(users.router)
app.include_router(feedback.router)
app.include_router(language.router)

# Serve uploaded files (accessible at /uploads/predictions/...)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def root():
    return {"message": "AgriMind Ethiopia API is running"}