# app/api/vi/dashboard.py
"""
Complete Dashboard API for AI Live Commerce Platform
Handles products, scripts, AI generation, MP3 creation, and personas
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
from app.services.ai_script_service import ai_script_service
from app.services.tts_service import tts_service
from app.utils.file_handler import file_handler
from app.core.exceptions import ValidationError, NotFoundError

class ValidationError(Exception): pass
class NotFoundError(Exception): pass
#ai_script_service = None
tts_service = None
class FileHandler:
    def __init__(self): pass
# file_handler = get_file_handler()


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

# Initialize file handler
file_handler = FileHandler()

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
        query = db.query(Product)
        
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
    """Generate AI scripts for a product"""
    try:
        # Validate product exists
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Validate persona exists
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == request.persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Script persona not found")
        
        # Generate scripts using AI service
        scripts = await ai_script_service.generate_scripts(
            db=db,
            product_id=request.product_id,
            persona_id=request.persona_id,
            mood=request.mood,
            count=request.count,
            custom_instructions=request.custom_instructions
        )
        
        return {
            "message": f"Generated {len(scripts)} AI scripts successfully",
            "scripts": scripts,
            "product_id": request.product_id,
            "persona_id": request.persona_id,
            "generation_details": {
                "mood": request.mood,
                "count": len(scripts),
                "persona_name": persona.name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
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
        
        if not script.can_edit:
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
        mp3_count = len(script.mp3_files)
        
        # Delete MP3 files from disk
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
    """Generate MP3 files from scripts"""
    try:
        # Validate scripts exist and are editable
        scripts = db.query(Script).filter(Script.id.in_(request.script_ids)).all()
        
        if len(scripts) != len(request.script_ids):
            raise HTTPException(status_code=404, detail="One or more scripts not found")
        
        # Validate voice persona
        voice_persona = db.query(VoicePersona).filter(VoicePersona.id == request.voice_persona_id).first()
        if not voice_persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        # Check if scripts already have MP3s
        scripts_with_mp3 = [s for s in scripts if s.has_mp3]
        if scripts_with_mp3:
            titles = [s.title for s in scripts_with_mp3]
            raise HTTPException(
                status_code=400, 
                detail=f"Scripts already have MP3 files: {', '.join(titles)}"
            )
        
        # Start MP3 generation in background
        background_tasks.add_task(
            _generate_mp3_background,
            request.script_ids,
            request.voice_persona_id,
            request.quality,
            db
        )
        
        return {
            "message": f"MP3 generation started for {len(scripts)} scripts",
            "scripts": [{"id": s.id, "title": s.title} for s in scripts],
            "voice_persona": voice_persona.name,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting MP3 generation: {str(e)}")

async def _generate_mp3_background(script_ids: List[int], voice_persona_id: int, quality: str, db: Session):
    """Background task for MP3 generation"""
    try:
        for script_id in script_ids:
            script = db.query(Script).filter(Script.id == script_id).first()
            voice_persona = db.query(VoicePersona).filter(VoicePersona.id == voice_persona_id).first()
            
            if script and voice_persona:
                # Generate MP3 using TTS service
                file_path, web_url = await tts_service.generate_script_audio(
                    script_id=str(script.id),
                    content=script.content,
                    language=script.language
                )
                
                if file_path and web_url:
                    # Create MP3 record
                    mp3_file = MP3File(
                        script_id=script.id,
                        filename=os.path.basename(file_path),
                        file_path=file_path,
                        voice_persona_id=voice_persona_id,
                        tts_provider=voice_persona.tts_provider,
                        voice_settings=voice_persona.get_tts_config(),
                        duration=script.estimated_speech_duration,
                        file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                        status="completed"
                    )
                    
                    db.add(mp3_file)
                    
                    # Mark script as having MP3
                    script.has_mp3 = True
                    script.is_editable = False
                    
                    # Update voice persona usage
                    voice_persona.usage_count += 1
                    
                    db.commit()
                    print(f"✅ Generated MP3 for script {script.id}: {script.title}")
                else:
                    print(f"❌ Failed to generate MP3 for script {script.id}")
                    
    except Exception as e:
        print(f"❌ Background MP3 generation error: {e}")
        db.rollback()

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
        
        personas = query.order_by(asc(ScriptPersona.sort_order), asc(ScriptPersona.name)).all()
        
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
        query = db.query(VoicePersona)
        
        if active_only:
            query = query.filter(VoicePersona.is_active == True)
            
        if provider:
            query = query.filter(VoicePersona.tts_provider == provider)
        
        personas = query.order_by(asc(VoicePersona.name)).all()
        
        return [persona.to_dict() for persona in personas]
        
    except Exception as e:
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
            ScriptPersona.usage_count
        ).filter(ScriptPersona.usage_count > 0).order_by(desc(ScriptPersona.usage_count)).limit(10).all()
        
        return {
            "period_days": days,
            "product_performance": [
                {
                    "product_id": stat.id,
                    "product_name": stat.name,
                    "script_count": stat.script_count,
                    "mp3_count": stat.mp3_count,
                    "completion_rate": (stat.mp3_count / max(stat.script_count, 1)) * 100 if stat.script_count else 0
                }
                for stat in product_stats
            ],
            "script_generation_trend": [
                {
                    "date": trend.date.isoformat(),
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