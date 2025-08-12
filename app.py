# app.py - Simple FastAPI server to get started
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
from pathlib import Path

# Import our models and database
from app.core.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.product import Product
from app.core.security import SecurityManager

# Create tables
Base.metadata.create_all(bind=engine)

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

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for API
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

class UserLogin(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    username: Optional[str] = None

# API Routes
@app.get("/")
async def root():
    """Serve the main dashboard"""
    index_path = Path("frontend/index.html")
    if index_path.exists():
        return FileResponse(str(index_path))
    return HTMLResponse(content="""
    <html>
        <head>
            <title>AI Live Commerce</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                .container {
                    background: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }
                .status {
                    background: #f0f0f0;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }
                .success {
                    color: green;
                    font-weight: bold;
                }
                a {
                    color: #667eea;
                    text-decoration: none;
                    font-weight: bold;
                }
                a:hover {
                    text-decoration: underline;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 AI Live Commerce Platform</h1>
                <div class="status">
                    <p class="success">✅ Server is running!</p>
                    <p>Database: Connected</p>
                    <p>Version: 1.0.0</p>
                </div>
                <h2>Quick Links:</h2>
                <ul>
                    <li><a href="/docs">📚 API Documentation</a></li>
                    <li><a href="/api/products">📦 View Products</a></li>
                    <li><a href="/api/health">🏥 Health Check</a></li>
                </ul>
                <h2>Demo Credentials:</h2>
                <p>Username: <code>demo</code></p>
                <p>Password: <code>demo123</code></p>
            </div>
        </body>
    </html>
    """)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }

@app.get("/api/products", response_model=List[ProductResponse])
async def get_products(db: Session = Depends(get_db)):
    """Get all products"""
    products = db.query(Product).filter(Product.is_active == True).all()
    return products

@app.post("/api/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """Create a new product"""
    # For now, use the demo user
    demo_user = db.query(User).filter(User.username == "demo").first()
    if not demo_user:
        raise HTTPException(status_code=404, detail="Demo user not found")
    
    # Check if SKU exists
    existing = db.query(Product).filter(Product.sku == product.sku).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    # Create product
    db_product = Product(
        **product.dict(),
        user_id=demo_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return db_product

@app.get("/api/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str, db: Session = Depends(get_db)):
    """Get a specific product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.delete("/api/products/{product_id}")
async def delete_product(product_id: str, db: Session = Depends(get_db)):
    """Delete a product (soft delete)"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    
    return {"message": "Product deleted successfully"}

@app.post("/api/login", response_model=LoginResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Simple login check (for demo)"""
    user = db.query(User).filter(User.username == credentials.username).first()
    
    if not user:
        return LoginResponse(success=False, message="User not found")
    
    if not SecurityManager.verify_password(credentials.password, user.hashed_password):
        return LoginResponse(success=False, message="Invalid password")
    
    return LoginResponse(
        success=True,
        message="Login successful",
        username=user.username
    )

# Mock endpoints for testing
@app.post("/api/mock/tiktok/connect")
async def mock_tiktok_connect():
    """Mock TikTok connection"""
    return {
        "success": True,
        "message": "Connected to TikTok Live (Mock Mode)",
        "stats": {
            "viewers": 0,
            "messages": 0
        }
    }

@app.post("/api/mock/facebook/connect")
async def mock_facebook_connect():
    """Mock Facebook connection"""
    return {
        "success": True,
        "message": "Connected to Facebook Live (Mock Mode)",
        "stream_key": "mock_stream_key_12345"
    }

# Add Avatar endpoints
@app.get("/avatar")
async def avatar_viewer():
    """Serve avatar viewer page"""
    avatar_path = Path("frontend/avatar.html")
    if avatar_path.exists():
        return FileResponse(str(avatar_path))
    return HTMLResponse("<h1>Avatar viewer not found</h1>")

@app.websocket("/ws/avatar")
async def websocket_avatar(websocket: WebSocket):
    """WebSocket for avatar control"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            # Echo back for now
            await websocket.send_json({
                "type": "response",
                "data": data
            })
    except WebSocketDisconnect:
        pass

@app.post("/api/avatar/speak")
async def avatar_speak(request: Request):
    """Make avatar speak"""
    data = await request.json()
    text = data.get("text", "")
    
    # Mock response for now
    return {
        "success": True,
        "text": text,
        "duration": len(text) * 0.05 + 1.0,
        "audio_url": None
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting AI Live Commerce Platform...")
    print("📱 Open browser at: http://localhost:8000")
    print("📚 API Docs at: http://localhost:8000/docs")
    print("\nPress CTRL+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)