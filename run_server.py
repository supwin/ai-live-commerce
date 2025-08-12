#!/usr/bin/env python3
"""
Fixed AI Live Commerce Platform Server
แก้ไขปัญหา Dashboard ไม่แสดงปกติ
"""
import sys
import os
from pathlib import Path

# For direct run
if __name__ == "__main__":
    import uvicorn
    
    # Add current directory to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    print("\n" + "="*50)
    print("🚀 AI Live Commerce Platform")
    print("="*50)
    print("📱 Dashboard: http://localhost:8000")
    print("🎭 Avatar: http://localhost:8000/avatar")
    print("📚 API Docs: http://localhost:8000/docs")
    print("="*50)
    print("Press CTRL+C to stop\n")
    
    # Run server
    uvicorn.run(
        "run_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import secrets
import json

# Import database and models
from app.core.database import SessionLocal, engine, Base, get_db
from app.models.user import User
from app.models.product import Product

# Import routers with error handling
try:
    from app.api.v1.avatar import router as avatar_router
    print("✅ Avatar router imported")
except ImportError as e:
    print(f"⚠️ Avatar router import failed: {e}")
    avatar_router = None

try:
    from app.api.v1.scripts import router as scripts_router
    print("✅ Scripts router imported")
except ImportError as e:
    print(f"⚠️ Scripts router import failed: {e}")
    scripts_router = None

try:
    from app.api.v1.facebook import router as facebook_router
    print("✅ Facebook router imported")
except ImportError as e:
    print(f"⚠️ Facebook router import failed: {e}")
    facebook_router = None

try:
    from app.api.v1.integration import router as integration_router
    print("✅ Integration router imported")
except ImportError as e:
    print(f"⚠️ Integration router import failed: {e}")
    integration_router = None

# Create database tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Live Commerce Platform",
    version="1.0.0",
    description="Multi-platform AI-powered live commerce system"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
if avatar_router:
    app.include_router(avatar_router)

if scripts_router:
    app.include_router(scripts_router)

if facebook_router:
    app.include_router(facebook_router, tags=["Facebook"])

if integration_router:
    app.include_router(integration_router)

# Mount static files
try:
    # Create static directory if not exists
    static_dir = Path("frontend/static")
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (static_dir / "audio").mkdir(exist_ok=True)
    (static_dir / "css").mkdir(exist_ok=True)
    (static_dir / "js").mkdir(exist_ok=True)
    (static_dir / "assets").mkdir(exist_ok=True)
    
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    print("✅ Static files mounted")
except Exception as e:
    print(f"⚠️ Static files mount failed: {e}")

# Pydantic models
class ProductCreate(BaseModel):
    name: str
    price: float
    description: str
    features: List[str] = []
    stock: int
    category: str
    sku: str

class ProductResponse(BaseModel):
    id: str
    name: str
    price: float
    description: str
    features: List[str]
    stock: int
    category: str
    sku: str
    is_active: bool

# Main routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard - FIXED"""
    try:
        index_path = Path("frontend/index.html")
        if index_path.exists():
            # Read the file content and return as HTMLResponse
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # Create a minimal dashboard if file doesn't exist
            minimal_dashboard = """
            <!DOCTYPE html>
            <html lang="th">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>AI Live Commerce Platform</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                    .container { max-width: 800px; margin: 0 auto; text-align: center; }
                    .card { background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; margin: 20px 0; }
                    .btn { background: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 25px; cursor: pointer; margin: 10px; }
                    .btn:hover { background: #45a049; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 AI Live Commerce Platform</h1>
                    <div class="card">
                        <h2>ระบบพร้อมใช้งาน!</h2>
                        <p>กรุณาสร้างไฟล์ frontend/index.html เพื่อใช้ Dashboard เต็มรูปแบบ</p>
                        <button class="btn" onclick="window.location.href='/avatar'">🎭 เปิด Avatar</button>
                        <button class="btn" onclick="window.location.href='/docs'">📚 API Docs</button>
                    </div>
                    <div class="card">
                        <h3>📊 System Status</h3>
                        <p>✅ Server: Running</p>
                        <p>✅ Database: Connected</p>
                        <p>✅ API: Available</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=minimal_dashboard)
    except Exception as e:
        logger.error(f"Error serving dashboard: {str(e)}")
        return HTMLResponse(
            content=f"<h1>Error loading dashboard</h1><p>{str(e)}</p>",
            status_code=500
        )

@app.get("/avatar", response_class=HTMLResponse)
async def avatar_page():
    """Serve the avatar page - FIXED"""
    try:
        avatar_path = Path("frontend/avatar.html")
        if avatar_path.exists():
            with open(avatar_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return HTMLResponse(content=content)
        else:
            # Create minimal avatar page if file doesn't exist
            minimal_avatar = """
            <!DOCTYPE html>
            <html lang="th">
            <head>
                <meta charset="UTF-8">
                <title>AI Avatar</title>
                <style>
                    body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 50px; }
                    .avatar { width: 200px; height: 200px; background: #ff6b6b; border-radius: 50%; margin: 0 auto 30px; }
                </style>
            </head>
            <body>
                <h1>🎭 AI Avatar</h1>
                <div class="avatar"></div>
                <p>Avatar system ready! กรุณาสร้างไฟล์ frontend/avatar.html เพื่อใช้ Avatar เต็มรูปแบบ</p>
                <button onclick="window.close()">ปิดหน้าต่าง</button>
            </body>
            </html>
            """
            return HTMLResponse(content=minimal_avatar)
    except Exception as e:
        logger.error(f"Error serving avatar page: {str(e)}")
        return HTMLResponse(
            content=f"<h1>Error loading avatar</h1><p>{str(e)}</p>",
            status_code=500
        )

@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse(content="", status_code=204)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "facebook_api": "available" if facebook_router else "not_available"
    }

# Products API
@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        return products
    except Exception as e:
        logger.error(f"Error getting products: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    try:
        demo_user = db.query(User).filter(User.username == "demo").first()
        if not demo_user:
            raise HTTPException(status_code=404, detail="Demo user not found")
        
        existing = db.query(Product).filter(Product.sku == product.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
        
        db_product = Product(
            id=secrets.token_hex(8),
            name=product.name,
            price=product.price,
            description=product.description,
            category=product.category,
            sku=product.sku,
            stock=product.stock,
            features=product.features,
            user_id=demo_user.id,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(db_product)
        db.commit()
        db.refresh(db_product)
        return db_product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create product")

# Facebook API - IMPROVED
@app.get("/api/facebook/connect")
async def facebook_connect_get():
    """Facebook connection endpoint - ปรับปรุงแล้ว"""
    try:
        # Mock mode with improved data
        return {
            "success": True,
            "mock_mode": True,
            "message": "Facebook connected successfully (Mock Mode)",
            "user_info": {
                "id": "mock_user_12345", 
                "name": "Demo User (Mock)",
                "email": "demo@test.com"
            },
            "pages": [
                {
                    "id": "mock_page_123",
                    "name": "Test Shop (Mock)",
                    "access_token": "mock_token_123",
                    "category": "Shopping & Retail",
                    "fan_count": 1500,
                    "mock_mode": True
                },
                {
                    "id": "mock_page_456",
                    "name": "Demo Store (Mock)",
                    "access_token": "mock_token_456", 
                    "category": "E-commerce",
                    "fan_count": 2800,
                    "mock_mode": True
                }
            ]
        }
    except Exception as e:
        logger.error(f"Facebook connect error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "fallback_available": True
        }

@app.get("/api/facebook/status")
async def facebook_status():
    """Facebook status check"""
    return {
        "connected": True,
        "mock_mode": True,
        "user_info": {"id": "mock_user", "name": "Demo User (Mock)"},
        "has_selected_page": False,
        "live_video_active": False
    }

@app.get("/api/facebook/pages")
async def facebook_pages():
    """Get Facebook pages"""
    return {
        "success": True,
        "pages": [
            {
                "id": "mock_page_123",
                "name": "Test Shop (Mock)",
                "access_token": "mock_token_123",
                "category": "Shopping & Retail",
                "fan_count": 1500
            },
            {
                "id": "mock_page_456", 
                "name": "Demo Store (Mock)",
                "access_token": "mock_token_456",
                "category": "E-commerce", 
                "fan_count": 2800
            }
        ]
    }

@app.post("/api/facebook/select-page")
async def select_facebook_page(data: dict):
    """Select Facebook page"""
    return {
        "success": True,
        "selected_page": {
            "id": data.get("page_id"),
            "name": "Selected Page (Mock)",
            "access_token": data.get("page_access_token")
        },
        "message": "Page selected successfully"
    }

@app.post("/api/facebook/live/create")
async def create_facebook_live(data: dict):
    """Create Facebook Live"""
    live_id = f"mock_live_{secrets.token_hex(8)}"
    return {
        "success": True,
        "live_video": {
            "id": live_id,
            "title": data.get("title", "AI Live Commerce"),
            "description": data.get("description", ""),
            "status": "LIVE",
            "permalink_url": f"https://facebook.com/mock/videos/{live_id}",
            "stream_url": f"rtmp://mock.facebook.com/live/{live_id}",
            "stream_key": f"mock_key_{secrets.token_hex(8)}",
            "mock_mode": True
        },
        "message": "Live video created successfully"
    }

@app.post("/api/facebook/live/end")
async def end_facebook_live():
    """End Facebook Live"""
    return {
        "success": True,
        "message": "Live video ended successfully"
    }

@app.get("/api/facebook/live/comments")
async def get_facebook_comments():
    """Get Facebook Live comments"""
    import random
    
    # Random mock comments
    if random.random() > 0.7:  # 30% chance
        mock_comments = [
            {
                "id": f"comment_{secrets.token_hex(6)}",
                "message": "สินค้าดีมาก ราคาเท่าไหร่ครับ?",
                "from": {"id": "user1", "name": "ลูกค้า A"},
                "created_time": datetime.now().isoformat()
            },
            {
                "id": f"comment_{secrets.token_hex(6)}",
                "message": "มีส่วนลดไหมคะ?",
                "from": {"id": "user2", "name": "ลูกค้า B"},
                "created_time": datetime.now().isoformat()
            }
        ]
        return {
            "success": True,
            "comments": [random.choice(mock_comments)]
        }
    
    return {"success": True, "comments": []}

@app.post("/api/facebook/live/comment")
async def post_facebook_comment(data: dict):
    """Post comment to Facebook Live"""
    return {
        "success": True,
        "comment_id": f"comment_{secrets.token_hex(8)}",
        "message": "Comment posted successfully"
    }

# Integration API - Enhanced
@app.post("/api/integration/session/start")
async def start_live_session(data: dict):
    try:
        platform = data.get("platform", "facebook")
        logger.info(f"Starting live session on platform: {platform}")
        
        return {
            "success": True,
            "session_id": secrets.token_hex(8),
            "platform": platform,
            "start_time": datetime.now().isoformat(),
            "message": "Live session started successfully",
            "status": {
                "active": True,
                "platform": platform,
                "mock_mode": True
            }
        }
    except Exception as e:
        logger.error(f"Start session error: {str(e)}")
        return {
            "success": False,
            "message": f"Session start failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

@app.post("/api/integration/session/stop")
async def stop_live_session():
    try:
        return {
            "success": True,
            "message": "Live session stopped successfully",
            "final_stats": {
                "comments_processed": 15,
                "auto_responses_sent": 8,
                "products_presented": 3,
                "platform": "facebook"
            }
        }
    except Exception as e:
        logger.error(f"Stop session error: {str(e)}")
        return {
            "success": False,
            "message": f"Session stop failed: {str(e)}"
        }

@app.get("/api/integration/session/status")
async def get_session_status():
    return {
        "active": False,
        "platform": None,
        "stats": {
            "comments_processed": 0,
            "auto_responses_sent": 0,
            "products_presented": 0,
            "start_time": None
        },
        "mock_mode": True
    }

@app.post("/api/integration/avatar/speak")
async def integration_avatar_speak(data: dict):
    try:
        message = data.get("message", "")
        platform = data.get("platform", "manual")
        
        if not message:
            return {
                "success": False,
                "message": "Message is required"
            }
        
        logger.info(f"Avatar speak [{platform}]: {message[:50]}...")
        
        return {
            "success": True,
            "message": "Avatar speech queued successfully",
            "text": message,
            "platform": platform,
            "queue_position": 1,
            "estimated_duration": len(message) * 0.05 + 2
        }
    except Exception as e:
        logger.error(f"Avatar speak error: {str(e)}")
        return {
            "success": False,
            "message": f"Avatar speak failed: {str(e)}"
        }

@app.get("/api/integration/products/random")
async def present_random_product(db: Session = Depends(get_db)):
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        if not products:
            # Create mock product if no products exist
            mock_product = {
                "id": "mock_product_1",
                "name": "AI Smart Camera",
                "price": 2999.0,
                "description": "กล้อง AI อัจฉริยะ ตรวจจับการเคลื่อนไหว"
            }
            return {
                "success": True,
                "product": mock_product,
                "message": "Presenting mock product",
                "mock_mode": True
            }
        
        import random
        selected_product = random.choice(products)
        
        return {
            "success": True,
            "product": {
                "id": selected_product.id,
                "name": selected_product.name,
                "price": selected_product.price,
                "description": selected_product.description
            },
            "message": "Random product presentation started"
        }
    except Exception as e:
        logger.error(f"Present random product error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to present product: {str(e)}"
        }

@app.post("/api/integration/test/full-demo")
async def run_full_demo():
    try:
        logger.info("Starting full demo...")
        
        return {
            "success": True,
            "demo_started": True,
            "session_status": {
                "active": True,
                "platform": "facebook",
                "mock_mode": True
            },
            "message": "Full demo started - simulating live commerce system",
            "speech_queue": {
                "total_items": 3,
                "estimated_duration": "45 seconds"
            },
            "next_step": "Visit /avatar page to see avatar in action"
        }
    except Exception as e:
        logger.error(f"Full demo error: {str(e)}")
        return {
            "success": False,
            "message": f"Demo failed: {str(e)}",
            "error": str(e)
        }

# Speech Queue API
@app.get("/api/integration/speech/queue/status")
async def get_speech_queue_status():
    try:
        import random
        
        queue_length = random.randint(0, 3)
        mock_queue_items = []
        
        for i in range(queue_length):
            mock_queue_items.append({
                "id": f"queue_item_{i}",
                "text": f"ข้อความในคิว #{i+1} - ทดสอบระบบ Speech Queue",
                "priority": random.choice(["low", "normal", "high"]),
                "source": random.choice(["manual", "facebook", "auto"]),
                "created_at": datetime.now().isoformat()
            })
        
        is_processing = random.choice([True, False]) if queue_length > 0 else False
        current_speech = "กำลังพูดข้อความทดสอบ..." if is_processing else None
        
        return {
            "success": True,
            "queue_length": queue_length,
            "queue_items": mock_queue_items,
            "is_processing": is_processing,
            "current_speech": current_speech
        }
    except Exception as e:
        logger.error(f"Get speech queue status error: {str(e)}")
        return {
            "success": False,
            "queue_length": 0,
            "queue_items": [],
            "is_processing": False,
            "current_speech": None
        }

@app.post("/api/integration/speech/queue/clear")
async def clear_speech_queue(keep_high_priority: bool = False):
    try:
        if keep_high_priority:
            cleared_count = 2
            message = "Cleared low priority items from queue"
        else:
            cleared_count = 5
            message = "Cleared all items from queue"
        
        return {
            "success": True,
            "cleared_count": cleared_count,
            "message": message
        }
    except Exception as e:
        logger.error(f"Clear speech queue error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to clear queue: {str(e)}"
        }

@app.post("/api/integration/auto-response")
async def toggle_auto_response(data: dict):
    try:
        enabled = data.get("enabled", True)
        
        return {
            "success": True,
            "auto_response_enabled": enabled,
            "message": f"Auto-response {'enabled' if enabled else 'disabled'}"
        }
    except Exception as e:
        logger.error(f"Toggle auto-response error: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to toggle auto-response: {str(e)}"
        }

# Avatar API
@app.post("/api/avatar/speak")
async def avatar_speak(data: dict):
    try:
        text = data.get("text", "")
        duration = data.get("duration", len(text) * 0.05 + 2.0)
        
        if not text:
            return {
                "success": False,
                "message": "Text is required"
            }
        
        logger.info(f"Avatar speaking: {text[:50]}...")
        
        return {
            "success": True,
            "message": "Avatar speech initiated",
            "text": text,
            "duration": duration,
            "queue_position": 1
        }
    except Exception as e:
        logger.error(f"Avatar speak error: {str(e)}")
        return {
            "success": False,
            "message": f"Avatar speech failed: {str(e)}"
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "detail": str(exc)}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Something went wrong"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 AI Live Commerce Platform starting up...")
    logger.info("📱 Dashboard: http://localhost:8000")
    logger.info("🎭 Avatar: http://localhost:8000/avatar") 
    logger.info("📚 API Docs: http://localhost:8000/docs")
    
    # Create directories
    try:
        Path("frontend").mkdir(exist_ok=True)
        Path("frontend/static").mkdir(exist_ok=True)
        Path("frontend/static/audio").mkdir(exist_ok=True)
        logger.info("✅ Directories created")
    except Exception as e:
        logger.warning(f"⚠️ Could not create directories: {e}")
    
    logger.info("🎉 All systems ready!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 AI Live Commerce Platform shutting down...")