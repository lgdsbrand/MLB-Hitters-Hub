"""
MLB Hitters Hub — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import hitters

app = FastAPI(
    title="MLB Hitters Hub API",
    description="Sports betting analytics API for MLB hitter projections",
    version="1.0.0",
)

# CORS — allow Next.js dev server and Vercel deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(hitters.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "MLB Hitters Hub API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
