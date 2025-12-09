"""FastAPI application entry point."""
import logging
from fastapi import FastAPI
from app.auth.api import http_routes
from app.api.websocket import websocket_routes
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_routes.router)
app.include_router(websocket_routes.router)

@app.get('/')
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "API is running"}