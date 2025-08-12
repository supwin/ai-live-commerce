# app/api/v1/scripts.py
"""
Scripts API endpoints with TTS support
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import random

from app.core.database import get_db
from app.models.product import Product
from app.models.script import ProductScript
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/scripts", tags=["scripts"])

# Request/Response models
class ScriptCreate(BaseModel):
    product_id: str
    title: str
    content: str
    script_type: str

class ScriptResponse(BaseModel):
    id: str
    product_id: str
    title: str
    content: str
    script_type: str
    usage_count: int
    is_active: bool
    audio_url: Optional[str] = None  # เพิ่ม audio URL

    class Config:
        from_attributes = True

class GeneratedScript(BaseModel):
    title: str
    content: str
    script_type: str

# Import AI service
try:
    from app.services.ai_script_service import AIScriptService
    ai_script_service = AIScriptService()
    print("✅ AI Script Service loaded successfully")
except ImportError as e:
    print(f"⚠️ AI Script Service import failed: {e}")
    ai_script_service = None
    
async def generate_product_scripts_ai(product: Product) -> List[GeneratedScript]:
    """Generate 3 different AI-powered scripts for a product"""
    try:
        # ใช้ AI สร้างสคริปต์
        ai_scripts = await ai_script_service.generate_ai_scripts(product)
        
        # Convert to GeneratedScript format
        scripts = []
        for script_data in ai_scripts:
            scripts.append(GeneratedScript(
                title=script_data["title"],
                content=script_data["content"],
                script_type=script_data["script_type"]
            ))
        
        return scripts
        
    except Exception as e:
        print(f"❌ AI script generation failed: {e}")
        # Fallback to template
        return generate_product_scripts_template(product)

def generate_product_scripts_template(product: Product) -> List[GeneratedScript]:
    """Generate template scripts (fallback)"""
    
    # Format price nicely
    price_text = f"{product.price:,.0f}"
    
    scripts = [
        GeneratedScript(
            title="แบบกระตุ้นความต้องการ",
            content=f"สวัสดีครับทุกคน! วันนี้เรามี {product.name} สุดพิเศษมาแนะนำ! {product.description} ในราคาเพียง {price_text} บาทเท่านั้น! ของดีแบบนี้หาได้ยากมาก รีบสั่งก่อนของหมดนะครับ! 🔥 สต็อกเหลือเพียง {product.stock} ชิ้นเท่านั้น!",
            script_type="emotional"
        ),
        GeneratedScript(
            title="แบบให้ข้อมูลละเอียด",
            content=f"ขอแนะนำ {product.name} ครับ ผลิตภัณฑ์คุณภาพเยี่ยมที่ {product.description} สิ่งที่ทำให้สินค้าชิ้นนี้พิเศษคือคุณภาพระดับพรีเมียม ในราคาที่จับต้องได้ เพียง {price_text} บาท หมวดหมู่ {product.category} ที่ได้รับความนิยมสุงสุด สต็อกมีจำนวนจำกัด เหลือเพียง {product.stock} ชิ้นเท่านั้น",
            script_type="informative"
        ),
        GeneratedScript(
            title="แบบสร้างปฏิสัมพันธ์",
            content=f"เฮ้ย! คนไหนกำลังหา {product.name} อยู่บ้าง? 🙋‍♀️ วันนี้เราเอาของดีมาให้ทุกคนแล้วนะ! {product.description} ราคาพิเศษสุดๆ {price_text} บาท! พิมพ์ 'สนใจ' ในแชทถ้าอยากได้นะครับ! ใครเป็นคนแรกจะได้ส่วนลดพิเศษ! 💝 มีเพียง {product.stock} ชิ้นเท่านั้น!",
            script_type="interactive"
        )
    ]
    
    return scripts

async def generate_audio_for_script(script: ProductScript):
    """Background task to generate audio for script"""
    try:
        await tts_service.generate_script_audio(
            script_id=script.id,
            content=script.content,
            language='th'
        )
    except Exception as e:
        print(f"❌ Failed to generate audio for script {script.id}: {e}")

@router.get("/generate/{product_id}")
async def generate_scripts(product_id: str, db: Session = Depends(get_db)):
    """Generate 3 AI-powered scripts for a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # ใช้ AI สร้างสคริปต์
    scripts = await generate_product_scripts_ai(product)
    return {"scripts": scripts}

@router.post("/save-multiple")
async def save_multiple_scripts(
    scripts_data: List[ScriptCreate], 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Save multiple scripts for a product and generate TTS audio"""
    if not scripts_data:
        raise HTTPException(status_code=400, detail="No scripts provided")
    
    saved_scripts = []
    product_id = scripts_data[0].product_id
    
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Save all scripts
    for script_data in scripts_data:
        # Create script
        script = ProductScript(
            product_id=script_data.product_id,
            title=script_data.title,
            content=script_data.content,
            script_type=script_data.script_type,
            usage_count=0,
            is_active=True
        )
        
        db.add(script)
        saved_scripts.append(script)
    
    try:
        db.commit()
        
        # Refresh all scripts to get IDs
        for script in saved_scripts:
            db.refresh(script)
            # Generate TTS audio in background
            background_tasks.add_task(generate_audio_for_script, script)
            
        return {
            "success": True,
            "message": f"บันทึกสคริปต์สำเร็จ {len(saved_scripts)} รายการ (กำลังสร้างไฟล์เสียง...)",
            "scripts": saved_scripts,
            "count": len(saved_scripts)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving scripts: {str(e)}")

@router.get("/product/{product_id}", response_model=List[ScriptResponse])
async def get_product_scripts(product_id: str, db: Session = Depends(get_db)):
    """Get all scripts for a product with audio URLs"""
    scripts = db.query(ProductScript).filter(
        ProductScript.product_id == product_id,
        ProductScript.is_active == True
    ).order_by(ProductScript.created_at.desc()).all()
    
    # Add audio URLs
    for script in scripts:
        script.audio_url = tts_service.get_script_audio_url(script.id)
    
    return scripts

@router.get("/product/{product_id}/random")
async def get_random_script(product_id: str, db: Session = Depends(get_db)):
    """Get a random script for a product (least used first)"""
    scripts = db.query(ProductScript).filter(
        ProductScript.product_id == product_id,
        ProductScript.is_active == True
    ).all()
    
    if not scripts:
        raise HTTPException(
            status_code=404, 
            detail="ยังไม่มีสคริปต์ที่บันทึกไว้ กรุณาสร้างและบันทึกสคริปต์ใหม่ก่อน"
        )
    
    # Find least used scripts
    min_usage = min(script.usage_count for script in scripts)
    least_used = [script for script in scripts if script.usage_count == min_usage]
    
    # Pick random from least used
    selected_script = random.choice(least_used)
    
    # Update usage count
    selected_script.usage_count += 1
    db.commit()
    db.refresh(selected_script)
    
    # Get audio URL
    audio_url = tts_service.get_script_audio_url(selected_script.id)
    
    return {
        "id": selected_script.id,
        "title": selected_script.title,
        "content": selected_script.content,
        "script_type": selected_script.script_type,
        "usage_count": selected_script.usage_count,
        "product_id": selected_script.product_id,
        "audio_url": audio_url
    }

@router.post("/generate-audio/{script_id}")
async def generate_script_audio(
    script_id: str, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate audio for a specific script"""
    script = db.query(ProductScript).filter(ProductScript.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # Generate audio in background
    background_tasks.add_task(generate_audio_for_script, script)
    
    return {
        "success": True,
        "message": "กำลังสร้างไฟล์เสียง...",
        "script_id": script_id
    }

@router.get("/audio-stats")
async def get_audio_stats():
    """Get TTS audio statistics"""
    stats = tts_service.get_audio_stats()
    return {
        "audio_files": stats["count"],
        "total_size_mb": stats["total_size_mb"],
        "storage_path": str(tts_service.audio_dir)
    }

@router.delete("/product/{product_id}")
async def delete_all_product_scripts(product_id: str, db: Session = Depends(get_db)):
    """Delete all scripts for a product and their audio files"""
    scripts = db.query(ProductScript).filter(
        ProductScript.product_id == product_id
    ).all()
    
    # Delete audio files
    for script in scripts:
        tts_service.delete_script_audio(script.id)
    
    # Delete from database
    deleted_count = db.query(ProductScript).filter(
        ProductScript.product_id == product_id
    ).delete()
    
    db.commit()
    
    return {
        "success": True,
        "message": f"ลบสคริปต์และไฟล์เสียงทั้งหมด {deleted_count} รายการ",
        "deleted_count": deleted_count
    }