# app/api/v1/video_generation.py
"""
Video Generation API Endpoints
สำหรับการสร้างวิดีโอจาก AI scripts
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ai_video_service import ai_video_service
from app.services.ai_script_service import ai_script_service
from app.models.product import Product
from app.models.script import Script

router = APIRouter(prefix="/video-generation", tags=["Video Generation"])

# Request Models
class VideoGenerationRequest(BaseModel):
    product_id: int
    script_id: Optional[int] = None  # หากไม่ระบุจะสร้าง script ใหม่
    video_style: str = "slideshow"  # slideshow, animated_text, product_showcase
    include_audio: bool = True
    persona_id: Optional[int] = None  # สำหรับสร้าง script ใหม่

class BatchVideoRequest(BaseModel):
    product_ids: List[int]
    video_style: str = "slideshow"
    include_audio: bool = True
    persona_id: Optional[int] = 1  # Default persona

class VideoUpdateRequest(BaseModel):
    video_id: str
    product_info: Optional[dict] = None

# Response Models
class VideoGenerationResponse(BaseModel):
    success: bool
    video_id: Optional[str] = None
    video_path: Optional[str] = None
    duration: Optional[float] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    has_audio: bool = False
    error: Optional[str] = None

@router.get("/status")
async def get_video_service_status():
    """ตรวจสอบสถานะของ Video Service"""
    
    try:
        status = ai_video_service.get_service_status()
        return {
            "success": True,
            "service_status": status,
            "ready_for_production": status["capabilities"]["video_generation"],
            "recommendations": [
                "✅ Service ready for video generation" if status["capabilities"]["video_generation"] else
                "📦 Install MoviePy and PIL for full video generation: pip install moviepy pillow",
                "🎬 Supports TikTok format (9:16 aspect ratio)",
                "🔊 TTS audio integration available",
                "🎨 Multiple video styles available"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/generate", response_model=VideoGenerationResponse)
async def generate_product_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    สร้างวิดีโอสินค้าจาก AI script
    
    Flow:
    1. ดึงข้อมูลสินค้า
    2. สร้าง/ดึง AI script
    3. สร้างวิดีโอ
    4. เพิ่ม TTS audio (หากต้องการ)
    """
    
    try:
        print(f"🎬 Video generation request for product {request.product_id}")
        
        # ตรวจสอบสินค้า
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {request.product_id} not found")
        
        print(f"   📦 Product: {product.name}")
        
        # ดึง/สร้าง script
        if request.script_id:
            # ใช้ script ที่มีอยู่
            script_obj = db.query(Script).filter(Script.id == request.script_id).first()
            if not script_obj:
                raise HTTPException(status_code=404, detail=f"Script {request.script_id} not found")
            
            script_data = {
                "title": script_obj.title,
                "content": script_obj.content,
                "call_to_action": script_obj.call_to_action,
                "target_emotion": script_obj.target_emotion
            }
            print(f"   📝 Using existing script: {script_obj.title}")
            
        else:
            # สร้าง script ใหม่ด้วย AI
            if not ai_script_service:
                raise HTTPException(status_code=503, detail="AI Script Service not available")
            
            if not request.persona_id:
                raise HTTPException(status_code=400, detail="persona_id required for new script generation")
            
            print(f"   🤖 Generating new AI script with persona {request.persona_id}")
            
            scripts = await ai_script_service.generate_scripts(
                db=db,
                product_id=request.product_id,
                persona_id=request.persona_id,
                count=1
            )
            
            if not scripts:
                raise HTTPException(status_code=500, detail="Failed to generate AI script")
            
            script_data = scripts[0]
            print(f"   ✅ Generated script: {script_data.get('title', 'Untitled')}")
        
        # เริ่มสร้างวิดีโอใน background
        background_tasks.add_task(
            generate_video_task,
            request.product_id,
            script_data,
            request.video_style,
            request.include_audio,
            db
        )
        
        # สร้าง video ID ล่วงหน้า
        import time
        video_id = f"product_{request.product_id}_{int(time.time() * 1000)}"
        
        return VideoGenerationResponse(
            success=True,
            video_id=video_id,
            video_path=f"/uploads/videos/{video_id}.mp4",
            format="mp4",
            resolution="1080x1920",
            has_audio=request.include_audio,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Video generation request failed: {str(e)}")
        return VideoGenerationResponse(
            success=False,
            error=str(e)
        )

async def generate_video_task(
    product_id: int,
    script_data: dict,
    video_style: str,
    include_audio: bool,
    db: Session
):
    """Background task สำหรับสร้างวิดีโอ"""
    
    try:
        print(f"🎬 Starting background video generation for product {product_id}")
        
        result = await ai_video_service.generate_product_video(
            product_id=product_id,
            script=script_data,
            db=db,
            video_style=video_style,
            include_audio=include_audio
        )
        
        if result.get("success"):
            print(f"✅ Background video generation completed: {result.get('video_path')}")
        else:
            print(f"❌ Background video generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Background video generation error: {str(e)}")

@router.post("/generate-batch")
async def generate_batch_videos(
    request: BatchVideoRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """สร้างวิดีโอสำหรับหลายสินค้าพร้อมกัน"""
    
    try:
        print(f"🎬 Batch video generation for {len(request.product_ids)} products")
        
        # ตรวจสอบสินค้าทั้งหมด
        products = db.query(Product).filter(Product.id.in_(request.product_ids)).all()
        found_ids = [p.id for p in products]
        missing_ids = [pid for pid in request.product_ids if pid not in found_ids]
        
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Products not found: {missing_ids}"
            )
        
        # เริ่ม batch generation
        video_jobs = []
        for product_id in request.product_ids:
            video_id = f"batch_{product_id}_{int(time.time() * 1000)}"
            
            background_tasks.add_task(
                generate_batch_video_task,
                product_id,
                request.video_style,
                request.include_audio,
                request.persona_id,
                video_id,
                db
            )
            
            video_jobs.append({
                "product_id": product_id,
                "video_id": video_id,
                "status": "queued"
            })
        
        return {
            "success": True,
            "message": f"Batch video generation started for {len(products)} products",
            "jobs": video_jobs,
            "estimated_completion": f"{len(products) * 2} minutes",
            "monitor_endpoint": "/api/v1/video-generation/batch-status"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Batch video generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_batch_video_task(
    product_id: int,
    video_style: str,
    include_audio: bool,
    persona_id: int,
    video_id: str,
    db: Session
):
    """Background task สำหรับ batch video generation"""
    
    try:
        print(f"🎬 Batch: Generating video for product {product_id}")
        
        # สร้าง AI script
        if ai_script_service and persona_id:
            scripts = await ai_script_service.generate_scripts(
                db=db,
                product_id=product_id,
                persona_id=persona_id,
                count=1
            )
            script_data = scripts[0] if scripts else {"content": "สินค้าดีราคาคุ้มค่า"}
        else:
            script_data = {"content": "สินค้าดีราคาคุ้มค่า"}
        
        # สร้างวิดีโอ
        result = await ai_video_service.generate_product_video(
            product_id=product_id,
            script=script_data,
            db=db,
            video_style=video_style,
            include_audio=include_audio
        )
        
        print(f"{'✅' if result.get('success') else '❌'} Batch video for product {product_id}: {result.get('video_path', 'Failed')}")
        
    except Exception as e:
        print(f"❌ Batch video generation error for product {product_id}: {str(e)}")

@router.get("/video/{video_id}/status")
async def get_video_status(video_id: str):
    """ตรวจสอบสถานะวิดีโอ"""
    
    try:
        status = await ai_video_service.get_video_status(video_id)
        return {
            "success": True,
            "video_status": status
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/styles")
async def get_available_video_styles():
    """รายการ video styles ที่มีให้เลือก"""
    
    return {
        "success": True,
        "video_styles": [
            {
                "id": "slideshow",
                "name": "Slideshow",
                "description": "สไลด์ภาพนิ่งพร้อมข้อความ เหมาะสำหรับแสดงข้อมูลสินค้า",
                "duration": "15-25 วินาที",
                "features": ["Title slide", "Product info", "Features", "Call to action"]
            },
            {
                "id": "animated_text",
                "name": "Animated Text",
                "description": "ข้อความเคลื่อนไหวบนพื้นหลังสี เหมาะสำหรับ content ที่เน้นข้อความ",
                "duration": "20-30 วินาที",
                "features": ["Text animation", "Fade effects", "Dynamic content"]
            },
            {
                "id": "product_showcase",
                "name": "Product Showcase",
                "description": "แสดงภาพสินค้าพร้อม highlight คุณสมบัติ เหมาะสำหรับสินค้าที่มีภาพ",
                "duration": "25-35 วินาที",
                "features": ["Product images", "Feature highlights", "Price emphasis", "Professional layout"]
            }
        ],
        "recommended": {
            "new_products": "product_showcase",
            "text_heavy": "animated_text",
            "general_purpose": "slideshow"
        }
    }

@router.post("/test-generation")
async def test_video_generation(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """ทดสอบการสร้างวิดีโอด้วยข้อมูล mock"""
    
    try:
        # สร้างข้อมูล mock
        mock_script = {
            "title": "ทดสอบสร้างวิดีโอ AI",
            "content": "สวัสดีครับ วันนี้มีสินค้าดีๆ มาแนะนำให้เพื่อนๆ ครับ สินค้าคุณภาพดี ราคาย่อมเยา ใช้งานได้จริง สั่งซื้อได้เลยครับ",
            "call_to_action": "สั่งซื้อได้เลยครับ อย่าลังเลเลย!",
            "target_emotion": "friendly"
        }
        
        # ใช้สินค้าตัวแรกที่เจอ หรือสร้างข้อมูล mock
        product = db.query(Product).first()
        if not product:
            # สร้าง mock product data
            mock_product_data = {
                "id": 999,
                "name": "ผลิตภัณฑ์ทดสอบ AI Video",
                "price": 299.00,
                "description": "สินค้าสำหรับทดสอบระบบสร้างวิดีโอ AI",
                "key_features": ["คุณภาพดี", "ราคาประหยัด", "ใช้งานง่าย", "ส่งฟรี"]
            }
            
            # สร้างวิดีโอด้วยข้อมูล mock
            result = await ai_video_service.generate_product_video(
                product_id=999,
                script=mock_script,
                db=db,
                video_style="slideshow",
                include_audio=True
            )
            
            return {
                "success": True,
                "message": "Test video generation completed",
                "result": result,
                "note": "Generated with mock product data",
                "mock_product": mock_product_data
            }
        else:
            # ใช้สินค้าจริง
            background_tasks.add_task(
                test_video_task,
                product.id,
                mock_script,
                db
            )
            
            return {
                "success": True,
                "message": "Test video generation started",
                "product": {
                    "id": product.id,
                    "name": product.name
                },
                "script": mock_script,
                "note": "Video generation running in background"
            }
            
    except Exception as e:
        print(f"❌ Test video generation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/list-videos")
async def list_videos():
    """List all generated videos"""
    try:
        video_dir = Path("frontend/uploads/videos")
        if not video_dir.exists():
            return {"videos": [], "count": 0}
        
        videos = []
        for video_file in video_dir.glob("*.mp4"):
            stat = video_file.stat()
            videos.append({
                "filename": video_file.name,
                "path": f"/uploads/videos/{video_file.name}",
                "size_mb": round(stat.st_size / (1024*1024), 2),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "duration": "Unknown"  # เพิ่ม video duration detection ในอนาคต
            })
        
        videos.sort(key=lambda x: x["created"], reverse=True)
        return {"videos": videos, "count": len(videos)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list videos: {str(e)}")

@router.delete("/delete-video/{filename}")
async def delete_video(filename: str):
    """Delete a video file"""
    try:
        video_path = Path(f"frontend/uploads/videos/{filename}")
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        if not filename.endswith('.mp4'):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        video_path.unlink()
        return {"message": f"Video {filename} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")

@router.post("/play-video/{filename}")
async def play_video(filename: str):
    """Play video on display server"""
    try:
        video_path = Path(f"frontend/uploads/videos/{filename}")
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Update content display with video
        from app.services.content_display_service import content_display_service
        
        await content_display_service.update_content({
            "type": "video",
            "video_path": f"/uploads/videos/{filename}",
            "title": filename.replace('.mp4', '').replace('_', ' ').title(),
            "status": "playing"
        })
        
        return {"message": f"Playing video: {filename}", "video_path": f"/uploads/videos/{filename}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to play video: {str(e)}")


async def test_video_task(product_id: int, mock_script: dict, db: Session):
    """Background task สำหรับทดสอบ"""
    
    try:
        result = await ai_video_service.generate_product_video(
            product_id=product_id,
            script=mock_script,
            db=db,
            video_style="slideshow",
            include_audio=True
        )
        
        print(f"🧪 Test video generation result: {result}")
        
    except Exception as e:
        print(f"❌ Test video generation error: {str(e)}")

@router.get("/recent-videos")
async def get_recent_videos():
    """ดูวิดีโอที่สร้างล่าสุด"""
    
    try:
        video_dir = ai_video_service.video_dir
        video_files = []
        
        if video_dir.exists():
            for file_path in video_dir.glob("*.mp4"):
                file_stat = file_path.stat()
                video_files.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size_mb": round(file_stat.st_size / (1024 * 1024), 2),
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "url": f"/uploads/videos/{file_path.name}"
                })
            
            # เรียงตามเวลาสร้างล่าสุด
            video_files.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "videos": video_files[:10],  # แสดง 10 ไฟล์ล่าสุด
            "total_videos": len(video_files),
            "video_directory": str(video_dir)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.delete("/video/{video_id}")
async def delete_video(video_id: str):
    """ลบวิดีโอ"""
    
    try:
        video_dir = ai_video_service.video_dir
        deleted_files = []
        
        # ค้นหาไฟล์ที่เกี่ยวข้องกับ video_id
        for file_path in video_dir.glob(f"{video_id}*"):
            file_path.unlink()
            deleted_files.append(str(file_path))
        
        if deleted_files:
            return {
                "success": True,
                "message": f"Deleted {len(deleted_files)} files",
                "deleted_files": deleted_files
            }
        else:
            return {
                "success": False,
                "message": "No files found to delete",
                "video_id": video_id
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }