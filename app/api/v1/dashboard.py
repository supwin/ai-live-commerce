# app/api/v1/dashboard.py
"""
Complete Dashboard API for AI Live Commerce Platform
Handles products, scripts, AI generation, MP3 creation, and personas
FIXED VERSION - All original functions preserved with proper imports
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.product import Product, ProductStatus
from app.models.script import Script, MP3File, Video, ScriptPersona, VoicePersona, ScriptType, ScriptStatus
from app.models.user import User

# Import services with proper error handling
try:
    from app.services.ai_script_service import ai_script_service
    print("✅ AI Script Service imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import AI Script Service: {e}")
    ai_script_service = None

try:
    from app.services.enhanced_tts_service import enhanced_tts_service as tts_service
    print("✅ Enhanced TTS Service imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import Enhanced TTS Service: {e}")
    from app.services.tts_service import tts_service
    print("✅ Fallback to basic TTS Service")

try:
    from app.utils.file_handler import file_handler
    print("✅ File Handler imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import File Handler: {e}")
    # Create mock file handler
    class MockFileHandler:
        def save_uploaded_file(self, file: UploadFile, subdirectory: str = ""):
            return f"/uploads/{subdirectory}/{file.filename}", file.filename
    file_handler = MockFileHandler()

try:
    from app.core.exceptions import ValidationError, NotFoundError
    print("✅ Exceptions imported successfully")
except ImportError as e:
    print(f"⚠️ Could not import custom exceptions: {e}")
    # Create basic exception classes
    class ValidationError(Exception):
        def __init__(self, message: str, field: str = None):
            self.message = message
            self.field = field
            super().__init__(message)
    
    class NotFoundError(Exception):
        def __init__(self, message: str):
            self.message = message
            super().__init__(message)

router = APIRouter()

# Pydantic models for request/response
class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    discount_percentage: int = Field(default=0, ge=0, le=100)
    category: Optional[str] = None
    brand: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    key_features: List[str] = Field(default_factory=list)
    selling_points: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    use_cases: List[str] = Field(default_factory=list)
    promotion_text: Optional[str] = None
    warranty_info: Optional[str] = None
    shipping_info: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ProductUpdateRequest(ProductCreateRequest):
    pass

class AIScriptGenerationRequest(BaseModel):
    product_id: int
    persona_id: int
    mood: str = Field(default="auto")
    count: int = Field(default=3, ge=1, le=10)
    custom_instructions: Optional[str] = None

class ManualScriptCreateRequest(BaseModel):
    product_id: int
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    target_emotion: Optional[str] = None
    call_to_action: Optional[str] = None

class ScriptUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_emotion: Optional[str] = None
    call_to_action: Optional[str] = None

class MP3GenerationRequest(BaseModel):
    script_ids: List[int]
    voice_persona_id: int
    quality: str = Field(default="medium")  # low, medium, high

class ScriptPersonaCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    speaking_style: Optional[str] = None
    target_audience: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    sample_phrases: List[str] = Field(default_factory=list)
    tone_guidelines: Optional[str] = None
    do_say: List[str] = Field(default_factory=list)
    dont_say: List[str] = Field(default_factory=list)
    default_emotion: str = Field(default="professional")
    available_emotions: List[str] = Field(default_factory=list)

class VoicePersonaCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tts_provider: str = Field(..., pattern="^(edge|google|elevenlabs)$")
    voice_id: str = Field(..., min_length=1)
    language: str = Field(default="th")
    gender: str = Field(default="female", pattern="^(male|female|neutral)$")
    age_range: Optional[str] = None
    accent: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[str] = None
    emotional_range: List[str] = Field(default_factory=list)
    provider_settings: Dict[str, Any] = Field(default_factory=dict)

# Dashboard Stats Endpoints
@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive dashboard statistics"""
    try:
        # Product statistics
        total_products = db.query(Product).count()
        active_products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
        out_of_stock = db.query(Product).filter(Product.status == ProductStatus.OUT_OF_STOCK).count()
        
        # Products ready for live streaming (have scripts and MP3s)
        products_with_content = db.query(Product).filter(
            Product.scripts.any(),
            Product.scripts.any(Script.has_mp3 == True)
        ).count()
        
        # Script statistics
        total_scripts = db.query(Script).count()
        ai_scripts = db.query(Script).filter(Script.script_type == ScriptType.AI_GENERATED).count()
        manual_scripts = db.query(Script).filter(Script.script_type == ScriptType.MANUAL).count()
        scripts_with_mp3 = db.query(Script).filter(Script.has_mp3 == True).count()
        
        # MP3 statistics
        total_mp3s = db.query(MP3File).count()
        mp3_size = db.query(func.sum(MP3File.file_size)).scalar() or 0
        mp3_duration = db.query(func.sum(MP3File.duration)).scalar() or 0
        
        # Video statistics
        total_videos = db.query(Video).count()
        video_size = db.query(func.sum(Video.file_size)).scalar() or 0
        
        # Persona statistics
        script_personas = db.query(ScriptPersona).filter(ScriptPersona.is_active == True).count()
        voice_personas = db.query(VoicePersona).filter(VoicePersona.is_active == True).count()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_products = db.query(Product).filter(Product.created_at >= week_ago).count()
        recent_scripts = db.query(Script).filter(Script.created_at >= week_ago).count()
        recent_mp3s = db.query(MP3File).filter(MP3File.created_at >= week_ago).count()
        
        return {
            "products": {
                "total": total_products,
                "active": active_products,
                "inactive": total_products - active_products,
                "out_of_stock": out_of_stock,
                "ready_for_live": products_with_content,
                "completion_rate": round((products_with_content / max(total_products, 1)) * 100, 1)
            },
            "content": {
                "scripts": total_scripts,
                "ai_scripts": ai_scripts,
                "manual_scripts": manual_scripts,
                "scripts_with_mp3": scripts_with_mp3,
                "mp3_files": total_mp3s,
                "videos": total_videos
            },
            "storage": {
                "mp3_size_mb": round(mp3_size / (1024 * 1024), 2) if mp3_size else 0,
                "video_size_mb": round(video_size / (1024 * 1024), 2) if video_size else 0,
                "total_mp3_duration_minutes": round(float(mp3_duration) / 60, 1) if mp3_duration else 0
            },
            "personas": {
                "script_personas": script_personas,
                "voice_personas": voice_personas
            },
            "recent_activity": {
                "new_products_week": recent_products,
                "new_scripts_week": recent_scripts,
                "new_mp3s_week": recent_mp3s
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

# AI Service Status Endpoint - NEW
@router.get("/dashboard/ai-status")
async def get_ai_service_status():
    """Get AI service connection status"""
    
    if not ai_script_service:
        return {
            "status": "unavailable",
            "message": "AI Script Service not loaded",
            "openai_configured": False,
            "mode": "simulation"
        }
    
    try:
        # Test OpenAI connection if available
        test_result = await ai_script_service.test_openai_connection()
        
        return {
            "status": "available",
            "message": "AI Script Service loaded",
            "openai_test": test_result,
            "mode": "openai" if test_result["status"] == "connected" else "simulation"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI Service error: {str(e)}",
            "openai_configured": False,
            "mode": "simulation"
        }

# Product Management Endpoints
@router.get("/dashboard/products")
async def get_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    has_scripts: Optional[bool] = None,
    has_mp3s: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get products with filtering and pagination"""
    try:
        print("🔍 DEBUG: Starting get_products API call") 
        query = db.query(Product)
        print("🔍 DEBUG: Created initial query") 
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
            
        if status:
            query = query.filter(Product.status == ProductStatus(status))
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Product.name.ilike(search_term)) |
                (Product.sku.ilike(search_term)) |
                (Product.description.ilike(search_term)) |
                (Product.brand.ilike(search_term))
            )
            
        if has_scripts is not None:
            if has_scripts:
                query = query.filter(Product.scripts.any())
            else:
                query = query.filter(~Product.scripts.any())
                
        if has_mp3s is not None:
            if has_mp3s:
                query = query.filter(Product.scripts.any(Script.has_mp3 == True))
            else:
                query = query.filter(~Product.scripts.any(Script.has_mp3 == True))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        products = query.order_by(desc(Product.created_at)).offset(offset).limit(limit).all()
        
        return {
            "products": [product.to_dict() for product in products],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ DETAILED ERROR in get_products: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@router.post("/dashboard/products")
async def create_product(product_data: ProductCreateRequest, db: Session = Depends(get_db)):
    """Create a new product"""
    try:
        # Check for duplicate SKU
        existing = db.query(Product).filter(Product.sku == product_data.sku).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Create product
        product = Product(
            sku=product_data.sku,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            original_price=product_data.original_price,
            discount_percentage=product_data.discount_percentage,
            category=product_data.category,
            brand=product_data.brand,
            stock_quantity=product_data.stock_quantity,
            key_features=product_data.key_features,
            selling_points=product_data.selling_points,
            target_audience=product_data.target_audience,
            use_cases=product_data.use_cases,
            promotion_text=product_data.promotion_text,
            warranty_info=product_data.warranty_info,
            shipping_info=product_data.shipping_info,
            tags=product_data.tags,
            status=ProductStatus.ACTIVE
        )
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        return product.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

@router.get("/dashboard/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details by ID"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@router.put("/dashboard/products/{product_id}")
async def update_product(product_id: int, product_data: ProductUpdateRequest, db: Session = Depends(get_db)):
    """Update product details"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Check for duplicate SKU (excluding current product)
        if product_data.sku != product.sku:
            existing = db.query(Product).filter(
                Product.sku == product_data.sku,
                Product.id != product_id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="SKU already exists")
        
        # Update fields
        for field, value in product_data.dict(exclude_unset=True).items():
            setattr(product, field, value)
        
        db.commit()
        db.refresh(product)
        
        return product.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@router.delete("/dashboard/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete product and all related data"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get counts for response
        scripts_count = len(product.scripts)
        mp3s_count = sum(len(script.mp3_files) for script in product.scripts)
        videos_count = len(product.videos)
        
        # Delete related files
        for script in product.scripts:
            for mp3 in script.mp3_files:
                if mp3.file_path and os.path.exists(mp3.file_path):
                    try:
                        os.remove(mp3.file_path)
                    except:
                        pass
        
        for video in product.videos:
            if video.file_path and os.path.exists(video.file_path):
                try:
                    os.remove(video.file_path)
                except:
                    pass
        
        # Delete product (cascades to scripts, MP3s, videos)
        db.delete(product)
        db.commit()
        
        return {
            "message": f"Product '{product.name}' deleted successfully",
            "deleted_items": {
                "scripts": scripts_count,
                "mp3_files": mp3s_count,
                "videos": videos_count
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

# Script Management Endpoints
@router.get("/dashboard/products/{product_id}/scripts")
async def get_product_scripts(product_id: int, db: Session = Depends(get_db)):
    """Get all scripts for a product"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        scripts = db.query(Script).filter(Script.product_id == product_id).order_by(desc(Script.created_at)).all()
        
        return [script.to_dict() for script in scripts]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching scripts: {str(e)}")

@router.post("/dashboard/scripts/generate-ai")
async def generate_ai_scripts(request: AIScriptGenerationRequest, db: Session = Depends(get_db)):
    """Generate AI scripts for a product - MAIN ENDPOINT WITH REAL OPENAI INTEGRATION"""
    try:
        # Validate product exists
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Validate persona exists
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == request.persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Script persona not found")
        
        # Check AI service availability
        if not ai_script_service:
            raise HTTPException(
                status_code=503, 
                detail="AI Script Service is not available. Please check OpenAI API configuration."
            )

        print(f"🎯 API Request: product_id={request.product_id}, persona_id={request.persona_id}, mood={request.mood}, count={request.count}")
        print(f"   Product: {product.name}")
        print(f"   Persona: {persona.name}")

        # Generate scripts using AI service - THIS WILL NOW CALL OPENAI
        scripts = await ai_script_service.generate_scripts(
            db=db,
            product_id=request.product_id,
            persona_id=request.persona_id,
            mood=request.mood,
            count=request.count,
            custom_instructions=request.custom_instructions
        )
        
        print(f"📊 Generated scripts count: {len(scripts)}")
        for i, script in enumerate(scripts):
            print(f"📄 Script {i+1}: {script.get('title', 'No title')[:50]}...")
        
        return {
            "message": f"Generated {len(scripts)} AI scripts successfully",
            "scripts": scripts,
            "product_id": request.product_id,
            "persona_id": request.persona_id,
            "generation_details": {
                "mood": request.mood,
                "count": len(scripts),
                "persona_name": persona.name,
                "ai_mode": "openai" if ai_script_service.client else "simulation"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating AI scripts: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating AI scripts: {str(e)}")

@router.post("/dashboard/scripts/manual")
async def create_manual_script(request: ManualScriptCreateRequest, db: Session = Depends(get_db)):
    """Create a manual script"""
    try:
        # Validate product exists
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Calculate duration estimate
        word_count = len(request.content.split())
        duration_estimate = max(30, int(word_count / 2.5))  # 2.5 words per second
        
        # Create script
        script = Script(
            product_id=request.product_id,
            title=request.title,
            content=request.content,
            script_type=ScriptType.MANUAL,
            language="th",
            target_emotion=request.target_emotion or "professional",
            call_to_action=request.call_to_action or "",
            duration_estimate=duration_estimate,
            status=ScriptStatus.DRAFT
        )
        
        db.add(script)
        db.commit()
        db.refresh(script)
        
        return script.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating manual script: {str(e)}")

@router.get("/dashboard/scripts/{script_id}")
async def get_script(script_id: int, db: Session = Depends(get_db)):
    """Get script details"""
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        return script.to_dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching script: {str(e)}")

@router.put("/dashboard/scripts/{script_id}")
async def update_script(script_id: int, request: ScriptUpdateRequest, db: Session = Depends(get_db)):
    """Update script content (only if editable)"""
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # Check if script can be edited
        if script.has_mp3:
            raise HTTPException(
                status_code=400, 
                detail="Script cannot be edited because it has MP3 files. Delete MP3s first to unlock editing."
            )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(script, field, value)
        
        # Recalculate duration if content changed
        if "content" in update_data:
            word_count = len(script.content.split())
            script.duration_estimate = max(30, int(word_count / 2.5))
        
        db.commit()
        db.refresh(script)
        
        return script.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating script: {str(e)}")


@router.delete("/dashboard/scripts/{script_id}")
async def delete_script(script_id: int, db: Session = Depends(get_db)):
    """Delete script and all related MP3 files"""
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        script_title = script.title
        mp3_count = len(script.mp3_files) if hasattr(script, 'mp3_files') else 0
        
        # Delete MP3 files from disk
        if hasattr(script, 'mp3_files'):
            for mp3 in script.mp3_files:
                if mp3.file_path and os.path.exists(mp3.file_path):
                    try:
                        os.remove(mp3.file_path)
                    except:
                        pass
        
        # Delete script (cascades to MP3 files)
        db.delete(script)
        db.commit()
        
        return {
            "message": f"Script '{script_title}' deleted successfully",
            "deleted_mp3_files": mp3_count
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting script: {str(e)}")

# MP3 Generation Endpoints
@router.post("/dashboard/mp3/generate")
async def generate_mp3(request: MP3GenerationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Generate MP3 files from scripts - Enhanced version"""
    try:
        # Validate scripts exist
        scripts = db.query(Script).filter(Script.id.in_(request.script_ids)).all()
        
        if len(scripts) != len(request.script_ids):
            missing_ids = set(request.script_ids) - {s.id for s in scripts}
            raise HTTPException(status_code=404, detail=f"Scripts not found: {missing_ids}")
        
        # Validate voice persona
        voice_persona = db.query(VoicePersona).filter(VoicePersona.id == request.voice_persona_id).first()
        if not voice_persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        # Check if scripts already have MP3s
        scripts_with_mp3 = [s for s in scripts if getattr(s, 'has_mp3', False)]
        if scripts_with_mp3:
            titles = [s.title for s in scripts_with_mp3]
            raise HTTPException(
                status_code=400, 
                detail=f"Scripts already have MP3 files: {', '.join(titles[:3])}{'...' if len(titles) > 3 else ''}"
            )
        
        print(f"🎵 Starting MP3 generation for {len(scripts)} scripts")
        print(f"   Voice: {voice_persona.name}")
        print(f"   Quality: {request.quality}")
        
        # Start MP3 generation in background
        background_tasks.add_task(
            _generate_mp3_background,
            request.script_ids,
            request.voice_persona_id,
            request.quality,
            db  # Pass current session for reference
        )
        
        return {
            "message": f"MP3 generation started for {len(scripts)} scripts",
            "scripts": [{"id": s.id, "title": s.title, "duration_estimate": s.duration_estimate} for s in scripts],
            "voice_persona": {
                "id": voice_persona.id,
                "name": voice_persona.name,
                "provider": voice_persona.tts_provider
            },
            "quality": request.quality,
            "status": "processing",
            "estimated_completion": f"{len(scripts) * 3} seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting MP3 generation: {str(e)}")

async def _generate_mp3_background(script_ids: List[int], voice_persona_id: int, quality: str, db_session: Session):
    """Enhanced background task for MP3 generation with emotional support"""
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        print(f"🎵 Starting Enhanced MP3 generation for {len(script_ids)} scripts")
        
        for script_id in script_ids:
            script = db.query(Script).filter(Script.id == script_id).first()
            voice_persona = db.query(VoicePersona).filter(VoicePersona.id == voice_persona_id).first()
            
            if script and voice_persona:
                try:
                    print(f"🎵 Generating Enhanced MP3 for script {script_id}: {script.title}")
                    
                    # เตรียม voice configuration
                    voice_config = {
                        "voice": voice_persona.voice_id,
                        "voice_id": voice_persona.voice_id,
                        "tts_provider": voice_persona.tts_provider,
                        "emotion": getattr(voice_persona, 'emotion', 'professional'),
                        "emotional_intensity": 1.2,  # เพิ่มความเข้มอารมณ์
                        "speed": float(voice_persona.speed),
                        "pitch": float(voice_persona.pitch),
                        "volume": float(voice_persona.volume)
                    }
                    
                    # กำหนดอารมณ์จาก script emotion
                    script_emotion = getattr(script, 'target_emotion', 'professional')
                    emotion_mapping = {
                        "excited": "cheerful",
                        "professional": "serious", 
                        "friendly": "gentle",
                        "confident": "serious",
                        "energetic": "cheerful",
                        "calm": "gentle",
                        "urgent": "angry"
                    }
                    mapped_emotion = emotion_mapping.get(script_emotion, "serious")
                    
                    print(f"   🎭 Using emotion: {script_emotion} → {mapped_emotion}")
                    print(f"   🔊 Provider: {voice_persona.tts_provider}")
                    print(f"   🗣️ Voice: {voice_persona.voice_id}")
                    
                    # Generate MP3 with enhanced TTS
                    if hasattr(tts_service, 'generate_emotional_speech'):
                        # ใช้ Enhanced TTS Service
                        file_path, web_url = await tts_service.generate_emotional_speech(
                            text=script.content,
                            script_id=str(script.id),
                            provider=voice_persona.tts_provider,
                            voice_config=voice_config,
                            emotion=mapped_emotion,
                            intensity=1.2,
                            language=getattr(script, 'language', 'th')
                        )
                    else:
                        # Fallback to basic TTS
                        file_path, web_url = await tts_service.generate_script_audio(
                            script_id=str(script.id),
                            content=script.content,
                            language=getattr(script, 'language', 'th'),
                            voice_persona=voice_config
                        )
                    
                    if file_path and web_url:
                        # Get file size
                        file_size = 0
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                        
                        # Create MP3 record with enhanced metadata
                        mp3_file = MP3File(
                            script_id=script.id,
                            filename=os.path.basename(file_path),
                            file_path=file_path,
                            voice_persona_id=voice_persona_id,
                            tts_provider=voice_persona.tts_provider,
                            voice_settings={
                                "speed": float(voice_persona.speed),
                                "pitch": float(voice_persona.pitch),
                                "volume": float(voice_persona.volume),
                                "quality": quality,
                                "emotion": mapped_emotion,
                                "emotion_intensity": 1.2,
                                "provider_config": voice_config
                            },
                            duration=getattr(script, 'duration_estimate', 60),
                            file_size=file_size,
                            status="completed"
                        )
                        
                        db.add(mp3_file)
                        
                        # Mark script as having MP3
                        script.has_mp3 = True
                        if hasattr(script, 'is_editable'):
                            script.is_editable = False
                        
                        # Update voice persona usage
                        if hasattr(voice_persona, 'usage_count'):
                            voice_persona.usage_count = getattr(voice_persona, 'usage_count', 0) + 1
                        
                        db.commit()
                        print(f"✅ Enhanced MP3 generated for script {script.id}: {script.title}")
                        print(f"   📁 File: {file_path}")
                        print(f"   📏 Size: {file_size} bytes")
                        print(f"   🎭 Emotion: {mapped_emotion}")
                        print(f"   ✅ Status: completed")
                    else:
                        print(f"❌ Failed to generate Enhanced MP3 for script {script.id}")
                        
                        # Create failed record
                        mp3_file = MP3File(
                            script_id=script.id,
                            filename=f"failed_{script.id}.mp3",
                            file_path="",
                            voice_persona_id=voice_persona_id,
                            tts_provider=voice_persona.tts_provider,
                            status="failed",
                            error_message="Enhanced TTS generation failed"
                        )
                        db.add(mp3_file)
                        db.commit()
                        
                except Exception as e:
                    print(f"❌ Error generating Enhanced MP3 for script {script_id}: {e}")
                    
                    # Create failed record
                    try:
                        mp3_file = MP3File(
                            script_id=script_id,
                            filename=f"error_{script_id}.mp3",
                            file_path="",
                            voice_persona_id=voice_persona_id,
                            tts_provider="unknown",
                            status="failed",
                            error_message=str(e)
                        )
                        db.add(mp3_file)
                        db.commit()
                    except:
                        pass
                    
                    db.rollback()
                    
        print(f"🎉 Enhanced MP3 generation completed for {len(script_ids)} scripts")
                    
    except Exception as e:
        print(f"❌ Enhanced background MP3 generation error: {e}")
        db.rollback()
    finally:
        db.close()

@router.get("/dashboard/tts/providers")
async def get_tts_providers():
    """Get available TTS providers and their capabilities"""
    try:
        if hasattr(tts_service, 'get_available_providers'):
            providers = tts_service.get_available_providers()
        else:
            # Fallback for basic TTS
            providers = {
                "basic": {
                    "available": True,
                    "voices": {"th": "Thai", "en": "English"},
                    "supports_emotions": False,
                    "quality": "basic",
                    "cost": "free"
                }
            }
        
        return {
            "providers": providers,
            "enhanced_tts": hasattr(tts_service, 'generate_emotional_speech'),
            "recommended": "edge" if providers.get("edge", {}).get("available") else "basic"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching TTS providers: {str(e)}")

# เพิ่ม endpoint สำหรับทดสอบ TTS
@router.post("/dashboard/tts/test")
async def test_tts_generation(
    text: str = "สวัสดีครับ ทดสอบระบบเสียงพูด",
    provider: str = "edge",
    emotion: str = "professional",
    voice_id: Optional[str] = None
):
    """Test TTS generation with different providers and emotions"""
    try:
        if not hasattr(tts_service, 'generate_emotional_speech'):
            raise HTTPException(status_code=501, detail="Enhanced TTS not available")
        
        # Use default voice if not specified
        if not voice_id:
            if provider == "edge":
                voice_id = "th-TH-PremwadeeNeural"
            elif provider == "elevenlabs":
                voice_id = "pNInz6obpgDQGcFmaJgB"
            else:
                voice_id = "default"
        
        voice_config = {"voice": voice_id, "voice_id": voice_id}
        
        # Generate test audio
        file_path, web_url = await tts_service.generate_emotional_speech(
            text=text,
            script_id="test",
            provider=provider,
            voice_config=voice_config,
            emotion=emotion,
            intensity=1.0,
            language="th"
        )
        
        if file_path and web_url:
            return {
                "success": True,
                "message": "Test TTS generation completed",
                "audio_url": web_url,
                "file_path": file_path,
                "provider": provider,
                "emotion": emotion,
                "voice_id": voice_id,
                "text_preview": text[:50] + "..." if len(text) > 50 else text
            }
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")

# เพิ่ม endpoint สำหรับดูอารมณ์ที่รองรับ
@router.get("/dashboard/tts/emotions/{provider}")
async def get_supported_emotions(provider: str):
    """Get supported emotions for a TTS provider"""
    try:
        if hasattr(tts_service, 'get_emotions_for_provider'):
            emotions = tts_service.get_emotions_for_provider(provider)
        else:
            emotions = ["neutral"]
        
        return {
            "provider": provider,
            "supported_emotions": emotions,
            "enhanced_tts": hasattr(tts_service, 'generate_emotional_speech')
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emotions: {str(e)}")


@router.delete("/dashboard/mp3/{mp3_id}")
async def delete_mp3(mp3_id: int, db: Session = Depends(get_db)):
    """Delete MP3 file and unlock script for editing"""
    try:
        mp3_file = db.query(MP3File).filter(MP3File.id == mp3_id).first()
        if not mp3_file:
            raise HTTPException(status_code=404, detail="MP3 file not found")
        
        script = mp3_file.script
        filename = mp3_file.filename
        
        # Delete file from disk
        if mp3_file.file_path and os.path.exists(mp3_file.file_path):
            try:
                os.remove(mp3_file.file_path)
            except:
                pass
        
        # Delete MP3 record
        db.delete(mp3_file)
        
        # Check if script has other MP3s
        remaining_mp3s = db.query(MP3File).filter(
            MP3File.script_id == script.id,
            MP3File.id != mp3_id
        ).count()
        
        # Unlock script if no more MP3s
        if remaining_mp3s == 0:
            script.has_mp3 = False
            if hasattr(script, 'is_editable'):
                script.is_editable = True
        
        db.commit()
        
        return {
            "message": f"MP3 file '{filename}' deleted successfully",
            "script_unlocked": remaining_mp3s == 0
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting MP3: {str(e)}")

@router.delete("/dashboard/scripts/{script_id}/mp3")
async def delete_script_mp3(script_id: int, db: Session = Depends(get_db)):
    """Delete all MP3 files for a specific script and unlock script for editing"""
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        # Get all MP3 files for this script
        mp3_files = db.query(MP3File).filter(MP3File.script_id == script_id).all()
        
        if not mp3_files:
            raise HTTPException(status_code=404, detail="No MP3 files found for this script")
        
        deleted_files = []
        
        # Delete each MP3 file
        for mp3_file in mp3_files:
            filename = mp3_file.filename
            
            # Delete file from disk
            if mp3_file.file_path and os.path.exists(mp3_file.file_path):
                try:
                    os.remove(mp3_file.file_path)
                    print(f"🗑️ Deleted file: {mp3_file.file_path}")
                except Exception as e:
                    print(f"⚠️ Failed to delete file {mp3_file.file_path}: {e}")
            
            # Delete MP3 record from database
            db.delete(mp3_file)
            deleted_files.append(filename)
        
        # Unlock script for editing
        script.has_mp3 = False
        if hasattr(script, 'is_editable'):
            script.is_editable = True
        
        db.commit()
        
        return {
            "message": f"Deleted {len(deleted_files)} MP3 file(s) for script '{script.title}'",
            "deleted_files": deleted_files,
            "script_unlocked": True,
            "script_id": script_id
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting script MP3s: {str(e)}")

# เพิ่ม endpoint สำหรับดู MP3 files ของ script
@router.get("/dashboard/scripts/{script_id}/mp3")
async def get_script_mp3_files(script_id: int, db: Session = Depends(get_db)):
    """Get all MP3 files for a specific script"""
    try:
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")
        
        mp3_files = db.query(MP3File).filter(MP3File.script_id == script_id).all()
        
        return {
            "script_id": script_id,
            "script_title": script.title,
            "mp3_files": [mp3.to_dict() for mp3 in mp3_files],
            "total_files": len(mp3_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching script MP3s: {str(e)}")



# Persona Management Endpoints
@router.get("/dashboard/personas/script")
async def get_script_personas(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get script personas"""
    try:
        query = db.query(ScriptPersona)
        
        if active_only:
            query = query.filter(ScriptPersona.is_active == True)
        
        personas = query.order_by(asc(getattr(ScriptPersona, 'sort_order', ScriptPersona.name)), asc(ScriptPersona.name)).all()
        
        return [persona.to_dict() for persona in personas]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching script personas: {str(e)}")

@router.post("/dashboard/personas/script")
async def create_script_persona(request: ScriptPersonaCreateRequest, db: Session = Depends(get_db)):
    """Create script persona"""
    try:
        # Check for duplicate name
        existing = db.query(ScriptPersona).filter(ScriptPersona.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Persona name already exists")
        
        persona = ScriptPersona(**request.dict())
        
        db.add(persona)
        db.commit()
        db.refresh(persona)
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating script persona: {str(e)}")

@router.get("/dashboard/personas/voice")
async def get_voice_personas(
    active_only: bool = True,
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get voice personas"""
    try:
        print("🔍 DEBUG: Starting get_voice_personas")
        query = db.query(VoicePersona)
        print("🔍 DEBUG: Created VoicePersona query")
        
        if active_only:
            query = query.filter(VoicePersona.is_active == True)
            print("🔍 DEBUG: Applied active filter")
            
        if provider:
            query = query.filter(VoicePersona.tts_provider == provider)
            print(f"🔍 DEBUG: Applied provider filter: {provider}")
        
        print("🔍 DEBUG: About to execute query")
        personas = query.order_by(asc(VoicePersona.name)).all()
        print(f"🔍 DEBUG: Found {len(personas)} personas")
        
        # Test each persona individually
        result = []
        for i, persona in enumerate(personas):
            try:
                print(f"🔍 DEBUG: Processing persona {i+1}: {persona.name}")
                print(f"🔍 DEBUG: Gender value: {persona.gender}")
                print(f"🔍 DEBUG: Gender type: {type(persona.gender)}")
                persona_dict = persona.to_dict()
                result.append(persona_dict)
                print(f"✅ DEBUG: Successfully processed persona {i+1}")
            except Exception as e:
                print(f"❌ DEBUG: Error processing persona {i+1} ({persona.name}): {e}")
                print(f"🔍 DEBUG: Persona data: id={persona.id}, gender={persona.gender}")
                raise e
        
        print("🔍 DEBUG: All personas processed successfully")
        return result
        
    except Exception as e:
        print(f"❌ ERROR in get_voice_personas: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching voice personas: {str(e)}")

@router.post("/dashboard/personas/voice")
async def create_voice_persona(request: VoicePersonaCreateRequest, db: Session = Depends(get_db)):
    """Create voice persona"""
    try:
        # Check for duplicate name
        existing = db.query(VoicePersona).filter(VoicePersona.name == request.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Voice persona name already exists")
        
        persona = VoicePersona(**request.dict())
        
        db.add(persona)
        db.commit()
        db.refresh(persona)
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating voice persona: {str(e)}")

# Analytics Endpoints
@router.get("/dashboard/analytics/summary")
async def get_analytics_summary(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get analytics summary for dashboard"""
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Product performance
        product_stats = db.query(
            Product.id,
            Product.name,
            func.count(Script.id).label('script_count'),
            func.count(MP3File.id).label('mp3_count')
        ).outerjoin(Script).outerjoin(MP3File).group_by(Product.id, Product.name).all()
        
        # Script generation trends
        script_trends = db.query(
            func.date(Script.created_at).label('date'),
            func.count(Script.id).label('count')
        ).filter(Script.created_at >= cutoff_date).group_by(func.date(Script.created_at)).all()
        
        # Persona usage
        persona_usage = db.query(
            ScriptPersona.name,
            func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0).label('usage_count')
        ).filter(
            func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0) > 0
        ).order_by(desc(func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0))).limit(10).all()
        
        return {
            "period_days": days,
            "product_performance": [
                {
                    "product_id": stat.id,
                    "product_name": stat.name,
                    "script_count": stat.script_count or 0,
                    "mp3_count": stat.mp3_count or 0,
                    "completion_rate": (stat.mp3_count / max(stat.script_count, 1)) * 100 if stat.script_count else 0
                }
                for stat in product_stats
            ],
            "script_generation_trend": [
                {
                    "date": trend.date.isoformat() if hasattr(trend.date, 'isoformat') else str(trend.date),
                    "scripts_generated": trend.count
                }
                for trend in script_trends
            ],
            "top_personas": [
                {
                    "persona_name": usage.name,
                    "usage_count": usage.usage_count
                }
                for usage in persona_usage
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

# Test Endpoints - NEW
@router.post("/dashboard/test/ai-generation")
async def test_ai_generation(db: Session = Depends(get_db)):
    """Test AI script generation with sample data"""
    
    if not ai_script_service:
        return {
            "status": "error",
            "message": "AI Script Service not available",
            "test_result": None
        }
    
    try:
        # Test OpenAI connection
        connection_test = await ai_script_service.test_openai_connection()
        
        return {
            "status": "success",
            "message": "AI generation test completed",
            "test_result": connection_test,
            "service_available": True,
            "recommendations": [
                "AI Script Service is loaded and ready",
                "Use /dashboard/scripts/generate-ai endpoint to generate scripts",
                "Check /dashboard/ai-status for real-time service status"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI generation test failed: {str(e)}",
            "test_result": None,
            "service_available": False
        }

# Categories endpoint for filtering - NEW
@router.get("/dashboard/categories")
async def get_categories(db: Session = Depends(get_db)):
    """Get available product categories"""
    try:
        categories = db.query(Product.category).filter(
            Product.category.isnot(None),
            Product.category != ""
        ).distinct().all()
        
        return [cat.category for cat in categories if cat.category]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

# Brands endpoint for filtering - NEW
@router.get("/dashboard/brands")
async def get_brands(db: Session = Depends(get_db)):
    """Get available product brands"""
    try:
        brands = db.query(Product.brand).filter(
            Product.brand.isnot(None),
            Product.brand != ""
        ).distinct().all()
        
        return [brand.brand for brand in brands if brand.brand]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching brands: {str(e)}")

# Export endpoint for backup - NEW
@router.get("/dashboard/export")
async def export_data(
    include_products: bool = True,
    include_scripts: bool = True,
    include_personas: bool = True,
    db: Session = Depends(get_db)
):
    """Export dashboard data for backup"""
    try:
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "2.0.0"
        }
        
        if include_products:
            products = db.query(Product).all()
            export_data["products"] = [product.to_dict() for product in products]
        
        if include_scripts:
            scripts = db.query(Script).all()
            export_data["scripts"] = [script.to_dict() for script in scripts]
        
        if include_personas:
            script_personas = db.query(ScriptPersona).all()
            voice_personas = db.query(VoicePersona).all()
            export_data["personas"] = {
                "script_personas": [persona.to_dict() for persona in script_personas],
                "voice_personas": [persona.to_dict() for persona in voice_personas]
            }
        
        return export_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")