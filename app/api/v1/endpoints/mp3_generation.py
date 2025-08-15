# app/api/v1/endpoints/mp3_generation.py
"""
MP3 Generation Endpoints
จัดการการสร้างไฟล์เสียงจากสคริปต์ด้วย TTS
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from ..dependencies import (
    get_db, validate_script_exists, validate_persona_exists,
    check_tts_service_availability, tts_service,
    Script, MP3File, VoicePersona,
    safe_file_delete, SUPPORTED_TTS_PROVIDERS, DEFAULT_VOICE_CONFIGS,
    handle_database_error, handle_service_error
)
from ..schemas import (
    MP3GenerationRequest, MP3FileResponse, TTSTestRequest, TTSTestResponse,
    SuccessResponse
)

router = APIRouter()

@router.post("/mp3/generate")
async def generate_mp3(
    request: MP3GenerationRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    สร้างไฟล์ MP3 จากสคริปต์ - Enhanced version พร้อม Emotional TTS
    
    Features:
    - Enhanced TTS with emotional support
    - Background processing
    - Clean metadata
    - Multiple quality levels
    - Progress tracking
    """
    try:
        # ตรวจสอบ scripts ที่ขอ
        scripts = db.query(Script).filter(Script.id.in_(request.script_ids)).all()
        
        if len(scripts) != len(request.script_ids):
            missing_ids = set(request.script_ids) - {s.id for s in scripts}
            raise HTTPException(
                status_code=404, 
                detail=f"Scripts not found: {list(missing_ids)}"
            )
        
        # ตรวจสอบ voice persona
        voice_persona = await validate_persona_exists(request.voice_persona_id, db, "voice")
        
        # ตรวจสอบ TTS service
        tts = check_tts_service_availability()
        
        # ตรวจสอบสคริปต์ที่มี MP3 แล้ว
        scripts_with_mp3 = [s for s in scripts if getattr(s, 'has_mp3', False)]
        if scripts_with_mp3:
            titles = [s.title for s in scripts_with_mp3]
            raise HTTPException(
                status_code=400, 
                detail=f"Scripts already have MP3 files: {', '.join(titles[:3])}{'...' if len(titles) > 3 else ''}"
            )
        
        print(f"🎵 Starting Enhanced MP3 generation for {len(scripts)} scripts")
        print(f"   🗣️ Voice: {voice_persona.name} ({voice_persona.tts_provider})")
        print(f"   🎚️ Quality: {request.quality}")
        
        # เริ่ม background generation
        background_tasks.add_task(
            _generate_mp3_background,
            request.script_ids,
            request.voice_persona_id,
            request.quality,
            db.get_bind().url,
            getattr(request, 'emotion', 'professional'),
            getattr(request, 'intensity', 1.0)
        )
        
        return {
            "message": f"MP3 generation started for {len(scripts)} scripts",
            "scripts": [
                {
                    "id": s.id, 
                    "title": s.title, 
                    "duration_estimate": getattr(s, 'duration_estimate', 60)
                } 
                for s in scripts
            ],
            "voice_persona": {
                "id": voice_persona.id,
                "name": voice_persona.name,
                "provider": voice_persona.tts_provider,
                "enhanced": hasattr(tts, 'generate_emotional_speech')
            },
            "quality": request.quality,
            "status": "processing",
            "estimated_completion": f"{len(scripts) * 3} seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "MP3 Generation")

async def _generate_mp3_background(
    script_ids: List[int], 
    voice_persona_id: int, 
    quality: str, 
    db_url: str,
    emotion: str = "professional",
    intensity: float = 1.0
):
    """
    Enhanced background task สำหรับการสร้าง MP3 พร้อม emotional support
    """
    from app.core.database import SessionLocal
    db = SessionLocal()
    
    try:
        print(f"🎵 Starting Enhanced MP3 background generation for {len(script_ids)} scripts")
        
        for script_id in script_ids:
            script = db.query(Script).filter(Script.id == script_id).first()
            voice_persona = db.query(VoicePersona).filter(VoicePersona.id == voice_persona_id).first()
            
            if script and voice_persona:
                try:
                    print(f"🎵 Generating Enhanced MP3 for script {script_id}: {script.title}")
                    
                    # เตรียม voice configuration พร้อม script title
                    voice_config = {
                        "voice": voice_persona.voice_id,
                        "voice_id": voice_persona.voice_id,
                        "tts_provider": voice_persona.tts_provider,
                        "emotion": getattr(voice_persona, 'emotion', 'professional'),
                        "emotional_intensity": 1.2,
                        "speed": float(voice_persona.speed),
                        "pitch": float(voice_persona.pitch),
                        "volume": float(voice_persona.volume),
                        "script_title": script.title  # 🆕 เพิ่ม script title สำหรับ metadata
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
                    print(f"   🏷️ Script Title: {script.title}")
                    
                    # สร้าง MP3 ด้วย Enhanced TTS
                    if hasattr(tts_service, 'generate_emotional_speech'):
                        file_path, web_url = await tts_service.generate_emotional_speech(
                            text=script.content,
                            script_id=str(script.id),
                            provider=voice_persona.tts_provider,
                            voice_config=voice_config,
                            emotion=mapped_emotion,
                            intensity=1.2,
                            language=getattr(script, 'language', 'th'),
                            script_title=script.title  # 🆕 ส่ง script title
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
                        # ดึงขนาดไฟล์
                        file_size = 0
                        if os.path.exists(file_path):
                            file_size = os.path.getsize(file_path)
                        
                        # สร้าง MP3 record พร้อม enhanced metadata
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
                                "provider_config": voice_config,
                                "script_title": script.title,  # 🆕 บันทึก script title
                                "metadata_cleaned": True  # 🆕 บันทึกว่าทำความสะอาด metadata แล้ว
                            },
                            duration=getattr(script, 'duration_estimate', 60),
                            file_size=file_size,
                            status="completed"
                        )
                        
                        db.add(mp3_file)
                        
                        # อัปเดตสคริปต์
                        script.has_mp3 = True
                        if hasattr(script, 'is_editable'):
                            script.is_editable = False
                        
                        # อัปเดต voice persona usage
                        if hasattr(voice_persona, 'usage_count'):
                            voice_persona.usage_count = getattr(voice_persona, 'usage_count', 0) + 1
                        
                        db.commit()
                        
                        print(f"✅ Enhanced MP3 generated successfully")
                        print(f"   📁 File: {file_path}")
                        print(f"   📦 Size: {file_size} bytes")
                        print(f"   🎭 Emotion: {mapped_emotion}")
                        print(f"   🏷️ Metadata: Clean")
                        
                    else:
                        print(f"❌ Failed to generate Enhanced MP3")
                        
                        # สร้าง failed record
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

@router.get("/tts/providers")
async def get_tts_providers():
    """
    ดึงรายการ TTS providers ที่ใช้ได้และความสามารถ
    """
    try:
        if hasattr(tts_service, 'get_available_providers'):
            providers = tts_service.get_available_providers()
        else:
            # Fallback สำหรับ basic TTS
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
            "recommended": "edge" if providers.get("edge", {}).get("available") else "basic",
            "supported_emotions": hasattr(tts_service, 'get_emotions_for_provider')
        }
        
    except Exception as e:
        handle_service_error(e, "TTS Providers")

@router.post("/tts/test", response_model=TTSTestResponse)
async def test_tts_generation(request: TTSTestRequest):
    """
    ทดสอบการสร้างเสียงพูด TTS พร้อมป้องกันการปนเปื้อน
    
    Features:
    - ทดสอบ TTS providers ต่างๆ
    - ทดสอบ emotions
    - ป้องกันการปนเปื้อนข้อมูล
    - วัดคุณภาพเสียง
    """
    try:
        print(f"🧪 TTS Test Request:")
        print(f"   📝 Text: '{request.text}'")
        print(f"   🎭 Emotion: {request.emotion}")
        print(f"   📊 Provider: {request.provider}")
        print(f"   🗣️ Voice ID: {request.voice_id}")
        
        tts = check_tts_service_availability()
        
        if not hasattr(tts, 'generate_emotional_speech'):
            raise HTTPException(status_code=501, detail="Enhanced TTS not available")
        
        # ใช้ default voice หากไม่ระบุ
        voice_id = request.voice_id or DEFAULT_VOICE_CONFIGS.get(request.provider, "default")
        
        voice_config = {"voice": voice_id, "voice_id": voice_id}
        
        print(f"   🎯 Processing text: '{request.text[:50]}...'")
        
        # ⚠️ ปัญหาหลัก: ต้องส่ง text parameter ที่ได้รับมา ไม่ใช่ hardcode
        file_path, web_url = await tts.generate_emotional_speech(
            text=request.text,  # 🔧 ใช้ text ที่ได้รับจาก request
            script_id="test_clean",
            provider=request.provider,
            voice_config=voice_config,
            emotion=request.emotion,
            intensity=1.0,
            language="th",
            script_title=f"TTS Test: {request.text[:30]}"  # 🔧 ใช้ text ในชื่อด้วย
        )
        
        if file_path and web_url:
            # ตรวจสอบคุณภาพไฟล์ที่สร้าง
            duration_seconds = 0
            try:
                if hasattr(tts, '_validate_and_clean_audio'):
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(file_path)
                        duration_seconds = len(audio) / 1000
                        print(f"   ⏱️ Generated audio duration: {duration_seconds:.1f}s")
                    except ImportError:
                        print(f"   ⏱️ pydub not available for duration check")
            except Exception as e:
                print(f"   ⚠️ Duration check failed: {e}")
            
            print(f"   ✅ TTS generation completed successfully")
            
            return {
                "success": True,
                "message": "Test TTS generation completed with contamination prevention",
                "audio_url": web_url,
                "file_path": file_path,
                "provider": request.provider,
                "emotion": request.emotion,
                "voice_id": voice_id,
                "text_preview": request.text[:50] + "..." if len(request.text) > 50 else request.text,
                "text_sent": request.text,  # 🔧 เพิ่มข้อมูล text ที่ส่งมา
                "duration_seconds": duration_seconds,
                "contamination_prevented": True
            }
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
            
    except Exception as e:
        print(f"❌ TTS test failed: {e}")
        handle_service_error(e, "TTS Test")

@router.get("/tts/emotions/{provider}")
async def get_supported_emotions(provider: str):
    """
    ดึงอารมณ์ที่รองรับสำหรับ TTS provider
    """
    try:
        if provider not in SUPPORTED_TTS_PROVIDERS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported provider. Valid options: {SUPPORTED_TTS_PROVIDERS}"
            )
        
        if hasattr(tts_service, 'get_emotions_for_provider'):
            emotions = tts_service.get_emotions_for_provider(provider)
        else:
            emotions = ["neutral"]
        
        return {
            "provider": provider,
            "supported_emotions": emotions,
            "enhanced_tts": hasattr(tts_service, 'generate_emotional_speech'),
            "default_emotion": "professional"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Get Emotions")

@router.delete("/mp3/{mp3_id}", response_model=SuccessResponse)
async def delete_mp3(mp3_id: int, db: Session = Depends(get_db)):
    """
    ลบไฟล์ MP3 และปลดล็อกสคริปต์สำหรับการแก้ไข
    """
    try:
        mp3_file = db.query(MP3File).filter(MP3File.id == mp3_id).first()
        if not mp3_file:
            raise HTTPException(status_code=404, detail="MP3 file not found")
        
        script = mp3_file.script
        filename = mp3_file.filename
        
        # ลบไฟล์จาก disk
        safe_file_delete(mp3_file.file_path)
        
        # ลบ MP3 record
        db.delete(mp3_file)
        
        # ตรวจสอบว่าสคริปต์มี MP3 อื่นอีกหรือไม่
        remaining_mp3s = db.query(MP3File).filter(
            MP3File.script_id == script.id,
            MP3File.id != mp3_id
        ).count()
        
        # ปลดล็อกสคริปต์หากไม่มี MP3 เหลือ
        if remaining_mp3s == 0:
            script.has_mp3 = False
            if hasattr(script, 'is_editable'):
                script.is_editable = True
        
        db.commit()
        
        return {
            "message": f"MP3 file '{filename}' deleted successfully",
            "success": True,
            "script_unlocked": remaining_mp3s == 0
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "delete_mp3")

@router.get("/mp3/status/{script_id}")
async def get_mp3_generation_status(script_id: int, db: Session = Depends(get_db)):
    """
    ตรวจสอบสถานะการสร้าง MP3 ของสคริปต์
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        mp3_files = db.query(MP3File).filter(MP3File.script_id == script_id).all()
        
        status_summary = {
            "script_id": script_id,
            "script_title": script.title,
            "has_mp3": getattr(script, 'has_mp3', False),
            "total_mp3_files": len(mp3_files),
            "mp3_files": []
        }
        
        for mp3 in mp3_files:
            mp3_info = {
                "id": mp3.id,
                "filename": mp3.filename,
                "status": mp3.status,
                "provider": mp3.tts_provider,
                "file_size": mp3.file_size,
                "duration": mp3.duration,
                "created_at": mp3.created_at.isoformat() if mp3.created_at else None
            }
            
            if mp3.status == "failed" and hasattr(mp3, 'error_message'):
                mp3_info["error_message"] = mp3.error_message
                
            status_summary["mp3_files"].append(mp3_info)
        
        return status_summary
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_mp3_generation_status")