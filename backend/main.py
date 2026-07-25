import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.routers import ai_companion, emergency, recovery, caregiver

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Multi-Modal GenAI Recovery & Prevention Platform Backend"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for web UI
if os.path.exists("src"):
    app.mount("/src", StaticFiles(directory="src"), name="src")

# Include Routers
app.include_router(ai_companion.router)
app.include_router(emergency.router)
app.include_router(recovery.router)
app.include_router(caregiver.router)

@app.get("/")
def read_root():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "message": "ResilienceAI Multi-Agent Backend Engine Running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

