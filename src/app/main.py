from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, analysis, vector_store, jobs
from app.services.model_manager import model_manager

app = FastAPI(title="Smart Document Assistant API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(vector_store.router, prefix="/api/vector-store", tags=["vector-store"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

@app.get("/")
async def root():
    return {"message": "Smart Document Assistant API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.on_event("startup")
async def startup_event():
    try:
        model_manager.warm_up_models()
        print("✅ Models initialized and warmed up successfully")
    except Exception as e:
        print(f"⚠️ Model warm-up failed: {e}")
