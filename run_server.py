#!/usr/bin/env python3
"""
AI Live Commerce Platform - Main Server
เซิร์ฟเวอร์หลักสำหรับ AI Live Commerce
"""

import uvicorn
import os
import sys
from pathlib import Path

# เพิ่ม project root ไปใน Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# โหลด environment variables
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    print("🚀 Starting AI Live Commerce Platform...")
    yield
    print("🛑 Shutting down AI Live Commerce Platform...")

# สร้าง FastAPI app
app = FastAPI(
    title="AI Live Commerce Platform",
    description="Platform สำหรับ Live Commerce ด้วย AI Avatar",
    version="2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ในการพัฒนา
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# Import และเพิ่ม routers
try:
    from app.api.v1.facebook import router as facebook_router
    app.include_router(facebook_router, prefix="/api/v1")
    print("✅ Facebook router imported")
except ImportError as e:
    print(f"⚠️ Facebook router import failed: {e}")

try:
    from app.api.v1.avatar import router as avatar_router
    app.include_router(avatar_router, prefix="/api/v1")
    print("✅ Avatar router imported")
except ImportError as e:
    print(f"⚠️ Avatar router import failed: {e}")

try:
    from app.api.v1.scripts import router as scripts_router
    app.include_router(scripts_router, prefix="/api/v1")
    print("✅ Scripts router imported")
except ImportError as e:
    print(f"⚠️ Scripts router import failed: {e}")

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Live Commerce Platform",
        "version": "2.0",
        "status": "running",
        "docs": "/docs",
        "avatar": "/avatar.html",
        "dashboard": "/index.html"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "AI Live Commerce",
        "version": "2.0"
    }

# เสิร์ฟ HTML files
from fastapi.responses import FileResponse

@app.get("/index.html")
async def serve_index():
    """เสิร์ฟหน้า dashboard"""
    return FileResponse("frontend/index.html")

@app.get("/avatar.html") 
async def serve_avatar():
    """เสิร์ฟหน้า avatar"""
    return FileResponse("frontend/avatar.html")

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 AI Live Commerce Platform")
    print("=" * 50)
    print("📱 Dashboard: http://localhost:8000")
    print("🎭 Avatar: http://localhost:8000/avatar")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("Press CTRL+C to stop")
    print()
    
    uvicorn.run(
        "run_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["app", "frontend"]
    )

# Redirect root to dashboard
from fastapi.responses import RedirectResponse

@app.get("/dashboard")
async def dashboard():
    """Redirect to dashboard"""
    return RedirectResponse(url="/index.html")


# Legal pages
@app.get("/privacy-policy")
async def privacy_policy():
    """Privacy Policy page"""
    return FileResponse("frontend/legal/privacy-policy.html")

@app.get("/terms-of-service")
async def terms_of_service():
    """Terms of Service page"""
    return FileResponse("frontend/legal/terms-of-service.html")


@app.get("/live-demo")
async def live_demo():
    """Live Streaming Demo"""
    return FileResponse("frontend/live-demo.html")

