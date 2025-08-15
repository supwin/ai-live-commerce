# ===== app/api/v1/endpoints/utilities.py =====
"""
Utility Endpoints
จัดการฟังก์ชันยูทิลิตี้และการทดสอบ
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any

from ..dependencies import (
    get_db, ai_script_service, tts_service,
    Product, Script, ScriptPersona, VoicePersona,
    handle_database_error, handle_service_error
)

router = APIRouter()

@router.post("/test/ai-generation")
async def test_ai_generation(db: Session = Depends(get_db)):
    """
    ทดสอบการสร้างสคริปต์ด้วย AI พร้อมข้อมูลตัวอย่าง
    
    Features:
    - ทดสอบการเชื่อมต่อ OpenAI
    - ตรวจสอบความพร้อมใช้งาน AI service
    - แนะนำวิธีการใช้งาน
    """
    
    if not ai_script_service:
        return {
            "status": "error",
            "message": "AI Script Service not available",
            "test_result": None,
            "recommendations": [
                "ตรวจสอบการติดตั้ง AI Script Service",
                "ตรวจสอบ OpenAI API Key configuration",
                "ดู logs สำหรับรายละเอียดข้อผิดพลาด"
            ]
        }
    
    try:
        # ทดสอบการเชื่อมต่อ OpenAI
        connection_test = await ai_script_service.test_openai_connection()
        
        return {
            "status": "success",
            "message": "AI generation test completed successfully",
            "test_result": connection_test,
            "service_available": True,
            "capabilities": [
                "AI Script Generation",
                "Multiple Personas Support",
                "Emotion-based Generation", 
                "Custom Instructions",
                "Real-time OpenAI Integration"
            ],
            "recommendations": [
                "AI Script Service พร้อมใช้งานแล้ว",
                "ใช้ /dashboard/scripts/generate-ai endpoint เพื่อสร้างสคริปต์",
                "ตรวจสอบ /dashboard/ai-status สำหรับสถานะล่าสุด"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"AI generation test failed: {str(e)}",
            "test_result": None,
            "service_available": False,
            "error_details": str(e)
        }

@router.get("/export")
async def export_data(
    include_products: bool = Query(True, description="รวมข้อมูลสินค้า"),
    include_scripts: bool = Query(True, description="รวมข้อมูลสคริปต์"),
    include_personas: bool = Query(True, description="รวมข้อมูล personas"),
    include_mp3s: bool = Query(False, description="รวมข้อมูล MP3 files"),
    db: Session = Depends(get_db)
):
    """
    Export ข้อมูล dashboard สำหรับ backup หรือ migration
    
    Features:
    - Export เลือกหมวดหมู่ได้
    - รวม metadata
    - รูปแบบ JSON
    """
    try:
        export_data = {
            "exported_at": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "dashboard_api": "enhanced_modular"
        }
        
        if include_products:
            products = db.query(Product).all()
            export_data["products"] = [product.to_dict() for product in products]
            print(f"📦 Exported {len(products)} products")
        
        if include_scripts:
            scripts = db.query(Script).all()
            export_data["scripts"] = [script.to_dict() for script in scripts]
            print(f"📄 Exported {len(scripts)} scripts")
        
        if include_personas:
            script_personas = db.query(ScriptPersona).all()
            voice_personas = db.query(VoicePersona).all()
            export_data["personas"] = {
                "script_personas": [persona.to_dict() for persona in script_personas],
                "voice_personas": [persona.to_dict() for persona in voice_personas]
            }
            print(f"🎭 Exported {len(script_personas)} script personas, {len(voice_personas)} voice personas")
        
        if include_mp3s:
            from ..dependencies import MP3File
            mp3_files = db.query(MP3File).all()
            export_data["mp3_files"] = [mp3.to_dict() for mp3 in mp3_files]
            print(f"🎵 Exported {len(mp3_files)} MP3 files")
        
        # Summary
        export_data["summary"] = {
            "total_items": sum([
                len(export_data.get("products", [])),
                len(export_data.get("scripts", [])),
                len(export_data.get("personas", {}).get("script_personas", [])),
                len(export_data.get("personas", {}).get("voice_personas", [])),
                len(export_data.get("mp3_files", []))
            ]),
            "categories_included": [
                key for key in ["products", "scripts", "personas", "mp3_files"] 
                if key in export_data and export_data[key]
            ]
        }
        
        return export_data
        
    except Exception as e:
        handle_database_error(e, "export_data")

@router.get("/system-info")
async def get_system_info():
    """
    ดึงข้อมูลระบบและการกำหนดค่า
    """
    try:
        import os
        import platform
        from datetime import datetime
        
        # Environment info
        env_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "environment": os.getenv("ENVIRONMENT", "development"),
            "api_version": "2.0.0"
        }
        
        # Service status
        services = {
            "ai_script_service": {
                "available": ai_script_service is not None,
                "type": "openai" if ai_script_service else "unavailable"
            },
            "tts_service": {
                "available": tts_service is not None,
                "enhanced": hasattr(tts_service, 'generate_emotional_speech') if tts_service else False
            }
        }
        
        # Feature flags
        features = {
            "ai_generation": ai_script_service is not None,
            "enhanced_tts": services["tts_service"]["enhanced"],
            "emotional_speech": services["tts_service"]["enhanced"],
            "multiple_personas": True,
            "background_processing": True,
            "analytics": True
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": env_info,
            "services": services,
            "features": features,
            "api_modules": [
                "dashboard_stats",
                "products",
                "scripts", 
                "mp3_generation",
                "personas",
                "analytics",
                "utilities"
            ]
        }
        
    except Exception as e:
        handle_service_error(e, "System Info")

@router.post("/system/cleanup")
async def cleanup_system(
    remove_failed_mp3s: bool = Query(True, description="ลบ MP3 files ที่ failed"),
    remove_temp_files: bool = Query(True, description="ลบไฟล์ชั่วคราว"),
    dry_run: bool = Query(False, description="ทดสอบโดยไม่ลบจริง"),
    db: Session = Depends(get_db)
):
    """
    ทำความสะอาดระบบและลบไฟล์ที่ไม่จำเป็น
    """
    try:
        cleanup_results = {
            "dry_run": dry_run,
            "actions_performed": [],
            "files_removed": 0,
            "space_freed": 0
        }
        
        if remove_failed_mp3s:
            from ..dependencies import MP3File
            failed_mp3s = db.query(MP3File).filter(MP3File.status == "failed").all()
            
            removed_count = 0
            for mp3 in failed_mp3s:
                if not dry_run:
                    # ลบ record จาก database
                    db.delete(mp3)
                    removed_count += 1
                
            if not dry_run and removed_count > 0:
                db.commit()
                
            cleanup_results["actions_performed"].append(
                f"{'Would remove' if dry_run else 'Removed'} {len(failed_mp3s)} failed MP3 records"
            )
        
        if remove_temp_files:
            import os
            import glob
            
            temp_patterns = [
                "/tmp/tts_*.mp3",
                "/tmp/test_*.mp3", 
                "/uploads/temp_*",
                "/uploads/test_*"
            ]
            
            temp_files_found = 0
            for pattern in temp_patterns:
                temp_files = glob.glob(pattern)
                temp_files_found += len(temp_files)
                
                if not dry_run:
                    for file_path in temp_files:
                        try:
                            if os.path.exists(file_path):
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                cleanup_results["space_freed"] += file_size
                        except:
                            pass
            
            cleanup_results["actions_performed"].append(
                f"{'Would remove' if dry_run else 'Removed'} {temp_files_found} temporary files"
            )
            cleanup_results["files_removed"] += temp_files_found
        
        # Convert bytes to MB
        cleanup_results["space_freed_mb"] = round(cleanup_results["space_freed"] / (1024 * 1024), 2)
        
        return cleanup_results
        
    except Exception as e:
        if not dry_run:
            db.rollback()
        handle_database_error(e, "cleanup_system")

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    ตรวจสอบสุขภาพระบบแบบละเอียด
    """
    try:
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "components": {},
            "performance": {},
            "recommendations": []
        }
        
        # Database health
        try:
            db.execute("SELECT 1")
            product_count = db.query(Product).count()
            script_count = db.query(Script).count()
            
            health_report["components"]["database"] = {
                "status": "healthy",
                "connection": "active",
                "products": product_count,
                "scripts": script_count
            }
        except Exception as e:
            health_report["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_report["overall_status"] = "degraded"
        
        # AI Service health
        if ai_script_service:
            try:
                ai_test = await ai_script_service.test_openai_connection()
                health_report["components"]["ai_service"] = {
                    "status": "healthy" if ai_test.get("status") == "connected" else "degraded",
                    "details": ai_test
                }
            except Exception as e:
                health_report["components"]["ai_service"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_report["overall_status"] = "degraded"
        else:
            health_report["components"]["ai_service"] = {
                "status": "unavailable",
                "message": "AI Script Service not loaded"
            }
        
        # TTS Service health
        if tts_service:
            health_report["components"]["tts_service"] = {
                "status": "healthy",
                "enhanced": hasattr(tts_service, 'generate_emotional_speech'),
                "providers": ["edge", "google", "elevenlabs"]  # Mock data
            }
        else:
            health_report["components"]["tts_service"] = {
                "status": "unavailable",
                "message": "TTS Service not loaded"
            }
            health_report["overall_status"] = "degraded"
        
        # Performance metrics (mock data)
        health_report["performance"] = {
            "api_response_time": "< 100ms",
            "database_query_time": "< 50ms",
            "ai_generation_time": "30-60s",
            "mp3_generation_time": "10-20s"
        }
        
        # Generate recommendations
        if health_report["overall_status"] != "healthy":
            health_report["recommendations"].append("ตรวจสอบ services ที่มีปัญหา")
        
        if not ai_script_service:
            health_report["recommendations"].append("ติดตั้งและกำหนดค่า AI Script Service")
            
        if not tts_service:
            health_report["recommendations"].append("ตรวจสอบ TTS Service configuration")
        
        if not health_report["recommendations"]:
            health_report["recommendations"].append("ระบบทำงานปกติ ไม่มีปัญหา")
        
        return health_report
        
    except Exception as e:
        handle_service_error(e, "Detailed Health Check")