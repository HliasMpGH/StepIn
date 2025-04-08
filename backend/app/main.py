import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.scheduler import scheduler

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Add CORS middleware with explicit origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Start the scheduler
scheduler.start()

# Serve static files - First priority to the Vue.js frontend
if os.path.exists("static/frontend"):
    app.mount("/static/frontend", StaticFiles(directory="static/frontend"), name="frontend")

# Serve static files - Fallback to the static directory
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Root endpoint to serve the UI
@app.get("/")
async def read_root():
    # Check if Vue.js frontend is available
    if os.path.exists("static/frontend/index.html"):
        return FileResponse("static/frontend/index.html")
    # Fallback to the original static HTML
    elif os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    # API message as last resort
    return {"message": f"{settings.PROJECT_NAME} API is running. Visit /docs for API documentation."}

@app.on_event("shutdown")
def shutdown_event():
    scheduler.stop()