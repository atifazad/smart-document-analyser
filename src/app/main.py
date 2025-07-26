from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import upload, analysis, vector_store
from app.services.model_manager import model_manager

app = FastAPI(title="Smart Document Assistant API")

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(analysis.router, prefix="/api/analysis")
app.include_router(vector_store.router, prefix="/api/vector-store")

@app.on_event("startup")
async def startup_event():
    """Initialize models on startup for better performance"""
    try:
        # Warm up models to reduce first-call latency
        model_manager.warm_up_models()
        print("✅ Models initialized and warmed up successfully")
    except Exception as e:
        print(f"⚠️ Model warm-up failed: {e}")

@app.get("/health")
def health_check():
    return {"status": "ok"}
