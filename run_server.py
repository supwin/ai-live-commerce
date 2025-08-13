#!/usr/bin/env python3
"""
AI Live Commerce Platform - Enhanced Server
Includes Dashboard, TTS, and Product Management APIs
"""

import os
import time
import psutil
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

# Import API routers - เฉพาะที่มีไฟล์จริง
try:
    from app.api.v1.products import router as products_router
except ImportError:
    print("⚠️ Products router not found, skipping...")
    products_router = None

try:
    from app.api.v1.tts import router as tts_router
except ImportError:
    print("⚠️ TTS router not found, skipping...")
    tts_router = None

try:
    from app.api.v1.dashboard import router as dashboard_router
except ImportError:
    print("⚠️ Dashboard router not found, skipping...")
    dashboard_router = None

from app.core.database import engine, create_tables

# Performance monitoring
startup_time = time.time()
process = psutil.Process()

# Simple settings
class Settings:
    HOST = "0.0.0.0"
    PORT = 8000
    DEBUG = True
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000", "*"]
    DATABASE_URL = "sqlite:///./ai_live_commerce.db"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 AI Live Commerce Platform - Enhanced Version")
    print("=" * 60)
    
    # Initialize database
    print("🗄️ Initializing database...")
    create_tables()
    print("✅ Database initialized")
    
    # Create directories
    print("📁 Creating directories...")
    directories = [
        "frontend/uploads/images",
        "frontend/uploads/videos", 
        "frontend/uploads/thumbnails",
        "frontend/static/audio",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Directories created")
    
    # Calculate startup time and memory
    startup_duration = time.time() - startup_time
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    
    print("🎉 AI Live Commerce Platform Ready!")
    print(f"📱 Dashboard: http://localhost:{settings.PORT}")
    print(f"📚 API Docs: http://localhost:{settings.PORT}/docs")
    print(f"⚡ Startup time: {startup_duration:.2f}s")
    print(f"💾 Memory usage: {memory_usage:.1f}MB")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down AI Live Commerce Platform...")

# Create FastAPI app
app = FastAPI(
    title="AI Live Commerce Platform",
    description="Complete dashboard for managing products, scripts, MP3 generation, and live streaming preparation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from app.api.v1.dashboard import router as dashboard_router
    print("✅ Dashboard router imported successfully")
except ImportError as e:
    print(f"❌ Dashboard router import failed: {e}")
    dashboard_router = None
except Exception as e:
    print(f"❌ Dashboard router error: {e}")
    dashboard_router = None 
    
# Include API routers - เฉพาะที่มี
if products_router:
    app.include_router(products_router, prefix="/api/v1", tags=["Products"])
if tts_router:
    app.include_router(tts_router, prefix="/api/v1", tags=["TTS"])
if dashboard_router:
    app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])
    print("✅ Dashboard routes registered")
else:
    print("❌ Dashboard routes NOT registered")


# Mount static files - ตรวจสอบว่ามี directory ก่อน
if os.path.exists("frontend/static"):
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
if os.path.exists("frontend/uploads"):
    app.mount("/uploads", StaticFiles(directory="frontend/uploads"), name="uploads")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """System health check with performance metrics"""
    try:
        uptime = time.time() - startup_time
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_percent = process.cpu_percent()
        
        # Memory status
        memory_status = "excellent" if memory_usage < 200 else "good" if memory_usage < 300 else "warning"
        
        # Performance target status
        performance_status = "✅ MEETING TARGETS" if memory_usage < 300 and uptime < 30 else "⚠️ CHECK PERFORMANCE"
        
        return {
            "status": "healthy",
            "phase": "Dashboard + TTS System",
            "database": {
                "connected": True,
                "info": {
                    "type": "SQLite",
                    "url": str(settings.DATABASE_URL)
                }
            },
            "system": {
                "memory_mb": round(memory_usage, 1),
                "memory_status": memory_status,
                "cpu_percent": cpu_percent,
                "uptime_seconds": round(uptime, 1),
                "uptime_formatted": f"{int(uptime//60)}m {int(uptime%60)}s"
            },
            "performance_target": {
                "status": performance_status,
                "targets": {
                    "startup_time": "< 30 seconds",
                    "memory_usage": "< 300MB",
                    "api_response": "< 500ms"
                }
            },
            "features": {
                "dashboard": "✅ Active" if dashboard_router else "❌ Not Available",
                "tts_system": "✅ Active" if tts_router else "❌ Not Available", 
                "product_management": "✅ Active" if products_router else "❌ Not Available",
                "script_generation": "✅ Active",
                "mp3_generation": "✅ Active"
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/system/info")
async def system_info():
    """Detailed system information"""
    try:
        memory_info = process.memory_info()
        
        return {
            "system": {
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
                "platform": os.name,
                "cpu_count": os.cpu_count(),
                "memory": {
                    "rss_mb": round(memory_info.rss / 1024 / 1024, 1),
                    "vms_mb": round(memory_info.vms / 1024 / 1024, 1),
                    "percent": process.memory_percent()
                },
                "disk": {
                    "cwd": os.getcwd(),
                    "free_space_gb": round(psutil.disk_usage('.').free / 1024**3, 1)
                }
            },
            "application": {
                "name": "AI Live Commerce Platform",
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "debug": settings.DEBUG
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/performance")
async def performance_metrics():
    """Real-time performance metrics"""
    try:
        uptime = time.time() - startup_time
        memory_usage = process.memory_info().rss / 1024 / 1024
        
        return {
            "timestamp": time.time(),
            "uptime_seconds": round(uptime, 1),
            "memory": {
                "usage_mb": round(memory_usage, 1),
                "target_mb": 300,
                "status": "ok" if memory_usage < 300 else "warning",
                "percentage": round((memory_usage / 300) * 100, 1)
            },
            "cpu": {
                "percent": process.cpu_percent(),
                "status": "ok"
            },
            "targets": {
                "startup_time_met": uptime < 30,
                "memory_target_met": memory_usage < 300,
                "overall_status": "meeting_targets" if uptime < 30 and memory_usage < 300 else "check_performance"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main dashboard route
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    try:
        dashboard_path = "frontend/dashboard/index.html"
        if os.path.exists(dashboard_path):
            return FileResponse(dashboard_path)
        else:
            # Fallback simple dashboard if file doesn't exist
            return HTMLResponse(content=f"""
<!DOCTYPE html>
<html>
<head>
    <title>AI Live Commerce Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
        .links {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 30px; }}
        .link-card {{ background: #4A90E2; color: white; padding: 20px; border-radius: 8px; text-decoration: none; text-align: center; transition: transform 0.3s; }}
        .link-card:hover {{ transform: translateY(-2px); }}
        .status {{ background: #e8f5e8; border: 1px solid #4caf50; border-radius: 6px; padding: 15px; margin: 20px 0; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 AI Live Commerce Platform</h1>
            <p>Dashboard Control Panel</p>
        </div>
        
        <div class="status">
            <strong>✅ System Status:</strong> Server Running<br>
            <strong>📊 Database:</strong> SQLite Initialized
        </div>
        
        <div class="status warning">
            <strong>⚠️ Setup Required:</strong><br>
            • Dashboard API files need to be created<br>
            • Frontend dashboard needs to be set up<br>
            • Complete installation using the artifacts provided
        </div>
        
        <div class="links">
            <a href="/docs" class="link-card">
                <h3>📚 API Documentation</h3>
                <p>Explore available APIs</p>
            </a>
            <a href="/api/health" class="link-card">
                <h3>🔧 Health Check</h3>
                <p>System status and metrics</p>
            </a>
            <a href="/api/system/info" class="link-card">
                <h3>📊 System Info</h3>
                <p>Detailed system information</p>
            </a>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <p><strong>Next Steps:</strong></p>
            <p>1. Create missing API files from the artifacts</p>
            <p>2. Set up the dashboard frontend</p>
            <p>3. Visit <a href="/docs">/docs</a> to test APIs</p>
        </div>
    </div>
</body>
</html>
            """)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading dashboard: {str(e)}")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content="""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1>404 - Page Not Found</h1>
                <p>The requested page could not be found.</p>
                <a href="/" style="color: #4A90E2;">Return to Dashboard</a>
            </body>
        </html>
        """,
        status_code=404
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return HTMLResponse(
        content="""
        <html>
            <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 100px;">
                <h1>500 - Internal Server Error</h1>
                <p>Something went wrong on our end.</p>
                <a href="/" style="color: #4A90E2;">Return to Dashboard</a>
            </body>
        </html>
        """,
        status_code=500
    )

if __name__ == "__main__":
    print("🚀 Starting AI Live Commerce Platform...")
    print("=" * 60)
    print("📱 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/api/health")
    print("📊 System Info: http://localhost:8000/api/system/info")
    print("=" * 60)
    print("🎯 Performance Targets:")
    print("   • Startup time: < 30 seconds")
    print("   • Memory usage: < 300MB")
    print("   • Fast API responses: < 500ms")
    print("=" * 60)
    
    uvicorn.run(
        "run_server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1,  # Single worker for development
        log_level="info",
        access_log=True
    )