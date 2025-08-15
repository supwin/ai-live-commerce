# run_server.py
"""
Enhanced AI Live Commerce Platform Server - With Real OpenAI Integration
Optimized for Core i7 + 8GB RAM with comprehensive dashboard system
"""

import os
import sys
import time
import psutil
import uvicorn
import asyncio
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings, print_startup_info, validate_openai_setup
from app.core.database import engine, SessionLocal, Base, create_tables
from app.models import *  # Import all models

# API Routers
from app.api.v1.dashboard import router as dashboard_router

# Import services to initialize them
try:
    from app.services.ai_script_service import ai_script_service
    print("✅ AI Script Service imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import AI Script Service: {e}")
    ai_script_service = None

try:
    from app.services.tts import enhanced_tts_service
    print("✅ Enhanced TTS Service imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import Enhanced TTS Service: {e}")
    enhanced_tts_service = None    

if enhanced_tts_service:
    tts_status = enhanced_tts_service.get_provider_status()
    print(f"   Available providers: {[p for p, s in tts_status.items() if s['available']]}")
    print(f"   Recommended provider: {enhanced_tts_service.get_recommended_provider()}")
    
# Global variables for monitoring
start_time = datetime.utcnow()
request_count = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    print("🚀 Starting AI Live Commerce Platform...")
    
    # Print startup information
    print_startup_info()
    
    # Validate OpenAI setup
    print("\n🔍 Validating OpenAI Integration...")
    openai_status = validate_openai_setup()
    if openai_status['configured']:
        print("✅ OpenAI integration configured properly")
    else:
        print("⚠️ OpenAI integration issues found:")
        for issue in openai_status['issues']:
            print(f"   - {issue}")
        print("💡 AI script generation will use simulation mode")
    
    # Initialize database
    print("\n🗄️ Initializing database...")
    try:
        create_tables()
        print("✅ Database tables initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Create required directories
    print("\n📁 Creating required directories...")
    directories = [
        "frontend/uploads/images",
        "frontend/uploads/videos", 
        "frontend/static/audio",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    # Test services
    print("\n🧪 Testing services...")
    if ai_script_service:
        try:
            connection_test = await ai_script_service.test_openai_connection()
            if connection_test["status"] == "connected":
                print("   ✅ OpenAI API connection successful")
            else:
                print(f"   ⚠️ OpenAI API: {connection_test['message']}")
        except Exception as e:
            print(f"   ⚠️ OpenAI test failed: {e}")
    else:
        print("   ⚠️ AI Script Service not available")

    print("\n🎤 Testing Thai TTS capabilities...")
    if enhanced_tts_service:
        try:
            providers = enhanced_tts_service.get_available_providers()
            available_count = sum(1 for p in providers.values() if p['available'])
            print(f"   ✅ TTS Providers available: {available_count}")
            for name, config in providers.items():
                if config['available']:
                    voices = len(config['voices'])
                    print(f"   ✅ {name.capitalize()}: {voices} voices, {config['quality']} quality")
        except Exception as e:
            print(f"   ⚠️ TTS test failed: {e}")    
    
    # Calculate startup time and memory usage
    startup_duration = (datetime.utcnow() - start_time).total_seconds()
    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    print("\n" + "=" * 80)
    print("🎉 AI Live Commerce Platform Ready!")
    print("=" * 80)
    print(f"📱 Dashboard: http://localhost:{get_settings().PORT}")
    print(f"📚 API Docs: http://localhost:{get_settings().PORT}/docs")  
    print(f"🔧 Health Check: http://localhost:{get_settings().PORT}/api/health")
    print(f"📊 System Info: http://localhost:{get_settings().PORT}/api/system/info")
    print("=" * 80)
    print(f"⚡ Startup time: {startup_duration:.2f}s")
    print(f"💾 Memory usage: {memory_usage:.1f}MB")
    print(f"🎯 Performance targets: {'✅ MEETING' if startup_duration < 30 and memory_usage < 300 else '⚠️ NOT MEETING'}")
    print("=" * 80)
    
    yield  # Application runs here
    
    # Cleanup on shutdown
    print("\n🛑 Shutting down AI Live Commerce Platform...")
    print("✅ Cleanup completed")

# Initialize FastAPI app
app = FastAPI(
    title="AI Live Commerce Platform",
    description="Advanced AI-powered live commerce platform with real-time script generation",
    version="2.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS.split(",") if isinstance(settings.ALLOWED_HOSTS, str) else settings.ALLOWED_HOSTS
    )

# Request counter middleware
@app.middleware("http")
async def count_requests(request: Request, call_next):
    global request_count
    request_count += 1
    start_time_req = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time_req
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/uploads", StaticFiles(directory="frontend/uploads"), name="uploads")

# Include API routers
app.include_router(dashboard_router, prefix="/api/v1", tags=["Dashboard"])
from app.api.v1.tts import router as tts_router
app.include_router(tts_router, prefix="/api/v1", tags=["Thai TTS"])

# Root endpoint - Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    try:
        dashboard_path = Path("frontend/dashboard/index.html")
        if dashboard_path.exists():
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                return HTMLResponse(content=f.read())
        else:
            # Fallback simple dashboard
            return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>AI Live Commerce Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #4A90E2; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { padding: 4px 8px; border-radius: 4px; font-size: 12px; }
        .status.success { background: #d4edda; color: #155724; }
        .status.warning { background: #fff3cd; color: #856404; }
        .btn { display: inline-block; padding: 8px 16px; background: #4A90E2; color: white; text-decoration: none; border-radius: 4px; }
        .btn:hover { background: #357abd; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 AI Live Commerce Dashboard</h1>
            <p>Advanced AI-powered live commerce platform with real-time script generation</p>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>🎯 Quick Actions</h3>
                <p><a href="/docs" class="btn">📚 API Documentation</a></p>
                <p><a href="/api/v1/dashboard/stats" class="btn">📊 Dashboard Stats</a></p>
                <p><a href="/api/v1/dashboard/ai-status" class="btn">🧠 AI Status</a></p>
                <p><a href="/api/v1/dashboard/test/ai-generation" class="btn">🧪 Test AI</a></p>
            </div>
            
            <div class="card">
                <h3>📋 System Status</h3>
                <p>Platform: <span class="status success">✅ Active</span></p>
                <p>Database: <span class="status success">✅ Connected</span></p>
                <p>AI Service: <span class="status warning">⚠️ Check Status</span></p>
            </div>
            
            <div class="card">
                <h3>🚀 Features Available</h3>
                <ul>
                    <li>✅ Product Management</li>
                    <li>✅ AI Script Generation</li>
                    <li>✅ TTS Integration</li>
                    <li>✅ Dashboard Analytics</li>
                    <li>✅ Persona Management</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>📞 Need Help?</h3>
                <p>📚 Check the <a href="/docs">API Documentation</a></p>
                <p>🧪 Run the <a href="/api/v1/dashboard/test/ai-generation">AI Test</a></p>
                <p>📊 Monitor <a href="/api/system/info">System Health</a></p>
            </div>

            <div class="card">
                <h3>🎤 Thai TTS System</h3>
                <p><a href="/api/v1/tts/test" class="btn">🧪 Test TTS</a></p>
                <p><a href="/api/v1/tts/voices" class="btn">🗣️ Available Voices</a></p>
                <p><a href="/api/v1/tts/status" class="btn">📊 TTS Status</a></p>
                <p><a href="/docs#/Thai%20TTS" class="btn">📚 TTS API Docs</a></p>
            </div>
        </div>
    </div>
    
    <script>
        // Auto-refresh system status
        async function updateStatus() {
            try {
                const response = await fetch('/api/v1/dashboard/ai-status');
                const status = await response.json();
                console.log('AI Status:', status);
            } catch (error) {
                console.error('Status check failed:', error);
            }
        }
        
        // Update status every 30 seconds
        setInterval(updateStatus, 30000);
        updateStatus(); // Initial check
    </script>
</body>
</html>
            """)
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error loading dashboard</h1><p>{str(e)}</p>", status_code=500)

# Health check endpoints
@app.get("/api/health")
async def health_check():
    """Enhanced health check"""
    
    # Get memory and CPU info
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    cpu_percent = process.cpu_percent()
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    # Check database connection
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_connected = True
        db_info = {
            "type": "SQLite",
            "size_mb": round(Path("ai_live_commerce.db").stat().st_size / (1024*1024), 2) if Path("ai_live_commerce.db").exists() else 0
        }
    except Exception as e:
        db_connected = False
        db_info = {"error": str(e)}
    
    # Check AI service status
    ai_status = "unavailable"
    ai_mode = "simulation"
    if ai_script_service:
        ai_status = "available"
        if ai_script_service.client:
            ai_mode = "openai"
        else:
            ai_mode = "simulation"
    
    # Performance assessment
    performance_status = "good"
    if memory_mb > 400:
        performance_status = "high_memory"
    elif uptime > 0 and uptime < 30:
        performance_status = "fast_startup"
    elif memory_mb < 250:
        performance_status = "excellent"
    
    performance_target = "✅ MEETING TARGETS" if memory_mb < 300 and uptime < 30 else "⚠️ CHECK PERFORMANCE"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "Dashboard + AI Integration",
        "version": "2.0.0",
        "features": {
            "dashboard": "✅ Active",
            "ai_integration": f"✅ Active ({ai_mode})",
            "tts_system": "✅ Active",
            "product_management": "✅ Active"
        },
        "database": {
            "connected": db_connected,
            "info": db_info
        },
        "system": {
            "memory_mb": round(memory_mb, 1),
            "cpu_percent": cpu_percent,
            "uptime_seconds": round(uptime, 1),
            "request_count": request_count,
            "memory_status": performance_status
        },
        "ai_service": {
            "status": ai_status,
            "mode": ai_mode,
            "available": ai_script_service is not None
        },
        "performance_target": {
            "status": performance_target,
            "memory_target": "< 300MB",
            "startup_target": "< 30 seconds"
        }
    }

@app.get("/api/system/info")
async def system_info():
    """Detailed system information"""
    
    process = psutil.Process()
    
    return {
        "application": {
            "name": "AI Live Commerce Platform", 
            "version": "2.0.0",
            "start_time": start_time.isoformat(),
            "uptime_seconds": (datetime.utcnow() - start_time).total_seconds()
        },
        "system": {
            "python_version": sys.version,
            "platform": sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_usage_gb": round(psutil.disk_usage('/').used / (1024**3), 2) if os.name != 'nt' else "N/A"
        },
        "process": {
            "pid": process.pid,
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()) if hasattr(process, 'open_files') else 0
        },
        "configuration": {
            "debug": settings.DEBUG,
            "host": settings.HOST,
            "port": settings.PORT,
            "workers": settings.WORKERS,
            "openai_configured": settings.is_openai_configured()
        },
        "services": {
            "ai_script_service": ai_script_service is not None,
            "openai_available": ai_script_service.client is not None if ai_script_service else False
        }
    }

@app.get("/api/system/performance")
async def system_performance():
    """Performance metrics"""
    
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    # Performance targets
    targets = {
        "startup_time_target": 30,  # seconds
        "memory_target": 300,       # MB
        "response_time_target": 500 # ms
    }
    
    # Current metrics
    metrics = {
        "memory_usage_mb": round(memory_mb, 1),
        "startup_time_seconds": round(uptime, 1) if uptime < 60 else "running",
        "cpu_percent": process.cpu_percent(),
        "request_count": request_count,
        "uptime_minutes": round(uptime / 60, 1)
    }
    
    # Performance assessment
    assessment = {
        "memory_status": "✅ Good" if memory_mb < targets["memory_target"] else "⚠️ High",
        "startup_status": "✅ Good" if uptime < targets["startup_time_target"] or uptime > 60 else "⚠️ Slow",
        "overall_status": "✅ Meeting Targets" if memory_mb < targets["memory_target"] else "⚠️ Check Performance"
    }
    
    return {
        "targets": targets,
        "current_metrics": metrics,
        "assessment": assessment,
        "recommendations": [
            "Memory usage is optimal" if memory_mb < 250 else "Consider memory optimization" if memory_mb > 400 else "Memory usage acceptable",
            "Performance targets met" if memory_mb < targets["memory_target"] else "Review memory usage patterns",
            f"Server has been running for {round(uptime/60, 1)} minutes"
        ]
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "available_endpoints": [
                "/",
                "/docs",
                "/api/health", 
                "/api/system/info",
                "/api/v1/dashboard/stats"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "type": type(exc).__name__,
            "path": str(request.url.path)
        }
    )

def main():
    """Main server entry point"""
    
    try:
        # Print banner
        print("=" * 80)
        print("🤖 AI Live Commerce Platform - Enhanced Server")
        print("=" * 80)
        print("🔧 Features: Real OpenAI Integration + Complete Dashboard")
        print("🎯 Optimized for: Intel Core i7 + 8GB RAM")
        print("📊 Phase: Dashboard + AI Script Generation")
        print("=" * 80)
        
        # Run the server
        uvicorn.run(
            "run_server:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG and settings.RELOAD == "true",
            workers=1 if settings.DEBUG else settings.WORKERS,
            log_level=settings.LOG_LEVEL.lower(),
            access_log=settings.DEBUG,
            loop="asyncio"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n💥 Server startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()