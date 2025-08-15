# app/api/v1/endpoints/dashboard_stats.py
"""
Dashboard Statistics Endpoints
จัดการข้อมูลสถิติและสถานะของระบบ
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..dependencies import (
    get_db, ai_script_service, tts_service,
    Product, ProductStatus, Script, ScriptType, MP3File, Video, ScriptPersona, VoicePersona,
    handle_database_error
)
from ..schemas import DashboardStatsResponse

router = APIRouter()

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    ดึงสถิติรวมของ Dashboard
    
    Returns:
        - สถิติสินค้า (จำนวน, สถานะ, ความพร้อม)
        - สถิติเนื้อหา (สคริปต์, MP3, วิดีโอ)
        - สถิติการจัดเก็บ (ขนาดไฟล์, ระยะเวลา)
        - สถิติ personas
        - กิจกรรมล่าสุด
    """
    try:
        # Product statistics
        total_products = db.query(Product).count()
        active_products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
        out_of_stock = db.query(Product).filter(Product.status == ProductStatus.OUT_OF_STOCK).count()
        
        # Products ready for live streaming (มีสคริปต์และ MP3)
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
        
        # Recent activity (7 วันที่ผ่านมา)
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
        handle_database_error(e, "get_dashboard_stats")

@router.get("/ai-status")
async def get_ai_service_status():
    """
    ตรวจสอบสถานะการเชื่อมต่อ AI Service
    
    Returns:
        - สถานะ AI Script Service
        - ผลการทดสอบ OpenAI connection
        - โหมดการทำงาน (openai/simulation)
    """
    
    if not ai_script_service:
        return {
            "status": "unavailable",
            "message": "AI Script Service not loaded",
            "openai_configured": False,
            "mode": "simulation",
            "recommendations": [
                "ตรวจสอบการติดตั้ง AI Script Service",
                "ตรวจสอบ OpenAI API Key configuration"
            ]
        }
    
    try:
        # ทดสอบการเชื่อมต่อ OpenAI
        test_result = await ai_script_service.test_openai_connection()
        
        return {
            "status": "available",
            "message": "AI Script Service loaded and ready",
            "openai_test": test_result,
            "mode": "openai" if test_result.get("status") == "connected" else "simulation",
            "capabilities": [
                "AI Script Generation",
                "Multiple Personas Support", 
                "Emotion-based Generation",
                "Custom Instructions"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"AI Service error: {str(e)}",
            "openai_configured": False,
            "mode": "simulation",
            "error_details": str(e)
        }

@router.get("/system-health")
async def get_system_health():
    """
    ตรวจสอบสุขภาพระบบโดยรวม
    
    Returns:
        - สถานะ AI Service
        - สถานะ TTS Service  
        - สถานะ Database
        - แนะนำการแก้ไข
    """
    health_status = {
        "overall": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
        "recommendations": []
    }
    
    # ตรวจสอบ AI Service
    if ai_script_service:
        try:
            ai_test = await ai_script_service.test_openai_connection()
            health_status["services"]["ai_service"] = {
                "status": "healthy" if ai_test.get("status") == "connected" else "degraded",
                "details": ai_test
            }
        except Exception as e:
            health_status["services"]["ai_service"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["overall"] = "degraded"
            health_status["recommendations"].append("ตรวจสอบ OpenAI API configuration")
    else:
        health_status["services"]["ai_service"] = {
            "status": "unavailable",
            "message": "AI Script Service not loaded"
        }
        health_status["overall"] = "degraded"
        health_status["recommendations"].append("ติดตั้งและกำหนดค่า AI Script Service")
    
    # ตรวจสอบ TTS Service
    if tts_service:
        health_status["services"]["tts_service"] = {
            "status": "healthy",
            "enhanced": hasattr(tts_service, 'generate_emotional_speech'),
            "providers": getattr(tts_service, 'available_providers', ['basic'])
        }
    else:
        health_status["services"]["tts_service"] = {
            "status": "unavailable",
            "message": "TTS Service not loaded"
        }
        health_status["overall"] = "degraded"
        health_status["recommendations"].append("ตรวจสอบ TTS Service configuration")
    
    # ตรวจสอบ Database
    try:
        from ..dependencies import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = {
            "status": "healthy",
            "connection": "active"
        }
        db.close()
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["overall"] = "critical"
        health_status["recommendations"].append("ตรวจสอบ Database connection")
    
    return health_status

@router.get("/performance-metrics")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """
    ดึงข้อมูลประสิทธิภาพระบบ
    
    Returns:
        - อัตราการสร้าง content
        - เวลาเฉลีย์ในการประมวลผล
        - อัตราความสำเร็จ
    """
    try:
        # คำนวณเมตริกต่างๆ ใน 30 วันที่ผ่านมา
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        # Script generation metrics
        scripts_generated = db.query(Script).filter(Script.created_at >= month_ago).count()
        ai_scripts_generated = db.query(Script).filter(
            Script.created_at >= month_ago,
            Script.script_type == ScriptType.AI_GENERATED
        ).count()
        
        # MP3 generation metrics
        mp3s_generated = db.query(MP3File).filter(MP3File.created_at >= month_ago).count()
        successful_mp3s = db.query(MP3File).filter(
            MP3File.created_at >= month_ago,
            MP3File.status == "completed"
        ).count()
        
        # Calculate success rates
        ai_success_rate = (ai_scripts_generated / max(scripts_generated, 1)) * 100
        mp3_success_rate = (successful_mp3s / max(mp3s_generated, 1)) * 100
        
        return {
            "period": "30 days",
            "script_generation": {
                "total_scripts": scripts_generated,
                "ai_scripts": ai_scripts_generated,
                "manual_scripts": scripts_generated - ai_scripts_generated,
                "daily_average": round(scripts_generated / 30, 1),
                "ai_adoption_rate": round(ai_success_rate, 1)
            },
            "mp3_generation": {
                "total_generated": mp3s_generated,
                "successful": successful_mp3s,
                "success_rate": round(mp3_success_rate, 1),
                "daily_average": round(mp3s_generated / 30, 1)
            },
            "efficiency": {
                "scripts_to_mp3_ratio": round((successful_mp3s / max(scripts_generated, 1)) * 100, 1),
                "automation_level": round(ai_success_rate, 1)
            }
        }
        
    except Exception as e:
        handle_database_error(e, "get_performance_metrics")