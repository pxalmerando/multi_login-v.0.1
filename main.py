"""FastAPI application entry point."""
from fastapi import FastAPI
from app.api import auth, url_processor


app = FastAPI()

# Include routers
app.include_router(auth.router, tags=["authentication"])
app.include_router(url_processor.router, tags=["url-processing"])


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}