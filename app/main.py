"""
FastAPI main application
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import router as api_router

# Initialize FastAPI app
app = FastAPI(
    title="Vibecode - Claude Opus Webapp",
    description="Web interface for Claude Opus 4.5",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files (frontend)
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Root route - serve the main HTML page
@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r") as f:
            return f.read()
    return "<h1>FRAMES</h1><p>No films yet.</p>"

# The Brutalist page
@app.get("/the-brutalist", response_class=HTMLResponse)
async def the_brutalist():
    html_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "the-brutalist.html")
    if os.path.exists(html_file):
        with open(html_file, "r") as f:
            return f.read()
    return "<h1>Not found</h1>"

# On the Silver Globe page
@app.get("/silver-globe", response_class=HTMLResponse)
async def silver_globe():
    html_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "silver-globe.html")
    if os.path.exists(html_file):
        with open(html_file, "r") as f:
            return f.read()
    return "<h1>Not found</h1>"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

