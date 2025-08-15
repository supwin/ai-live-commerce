# app/api/v1/endpoints/personas.py
"""
Persona Management Endpoints
จัดการ Script Personas และ Voice Personas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional

from ..dependencies import (
    get_db, ScriptPersona, VoicePersona,
    handle_database_error, SUPPORTED_TTS_PROVIDERS
)
from ..schemas import (
    ScriptPersonaCreateRequest, VoicePersonaCreateRequest,
    PersonaResponse, SuccessResponse
)

router = APIRouter()

# Script Persona Endpoints
@router.get("/personas/script")
async def get_script_personas(
    active_only: bool = Query(True, description="แสดงเฉพาะ personas ที่ใช้งานได้"),
    search: Optional[str] = Query(None, description="ค้นหาจากชื่อหรือคำอธิบาย"),
    db: Session = Depends(get_db)
):
    """
    ดึงรายการ Script Personas
    
    Features:
    - กรองตาม active status
    - ค้นหาจากชื่อและคำอธิบาย
    - เรียงลำดับตาม sort_order และชื่อ
    """
    try:
        print("🔍 DEBUG: Starting get_script_personas")
        query = db.query(ScriptPersona)
        
        if active_only:
            query = query.filter(ScriptPersona.is_active == True)
            
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (ScriptPersona.name.ilike(search_term)) |
                (ScriptPersona.description.ilike(search_term)) |
                (ScriptPersona.speaking_style.ilike(search_term))
            )
        
        personas = query.order_by(
            asc(getattr(ScriptPersona, 'sort_order', ScriptPersona.name)), 
            asc(ScriptPersona.name)
        ).all()
        
        result = []
        for persona in personas:
            persona_dict = persona.to_dict()
            
            # เพิ่มสถิติการใช้งาน
            usage_count = getattr(persona, 'usage_count', 0)
            persona_dict['usage_count'] = usage_count
            
            result.append(persona_dict)
        
        print(f"✅ Found {len(result)} script personas")
        return result
        
    except Exception as e:
        handle_database_error(e, "get_script_personas")

@router.post("/personas/script", response_model=PersonaResponse)
async def create_script_persona(
    request: ScriptPersonaCreateRequest, 
    db: Session = Depends(get_db)
):
    """
    สร้าง Script Persona ใหม่
    
    Features:
    - ตรวจสอบชื่อซ้ำ
    - ตั้งค่าเริ่มต้น
    - ตรวจสอบความถูกต้องของ system prompt
    """
    try:
        # ตรวจสอบชื่อซ้ำ
        existing = db.query(ScriptPersona).filter(ScriptPersona.name == request.name).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Script persona name '{request.name}' already exists"
            )
        
        # ตรวจสอบ system prompt
        if len(request.system_prompt) < 10:
            raise HTTPException(
                status_code=400,
                detail="System prompt must be at least 10 characters long"
            )
        
        persona_data = request.dict()
        persona_data['is_active'] = True
        persona_data['usage_count'] = 0
        
        persona = ScriptPersona(**persona_data)
        
        db.add(persona)
        db.commit()
        db.refresh(persona)
        
        print(f"✅ Created script persona: {persona.name}")
        print(f"   📝 System prompt length: {len(request.system_prompt)} chars")
        print(f"   🎭 Default emotion: {request.default_emotion}")
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "create_script_persona")

@router.get("/personas/script/{persona_id}")
async def get_script_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูล Script Persona ตาม ID พร้อมสถิติการใช้งาน
    """
    try:
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Script persona not found")
        
        persona_dict = persona.to_dict()
        
        # เพิ่มสถิติการใช้งาน
        from ..dependencies import Script
        scripts_generated = db.query(Script).filter(
            getattr(Script, 'persona_id', None) == persona_id
        ).count()
        
        persona_dict['scripts_generated'] = scripts_generated
        persona_dict['usage_count'] = getattr(persona, 'usage_count', 0)
        
        return persona_dict
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_script_persona")

@router.put("/personas/script/{persona_id}")
async def update_script_persona(
    persona_id: int,
    request: ScriptPersonaCreateRequest,
    db: Session = Depends(get_db)
):
    """
    อัปเดต Script Persona
    """
    try:
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Script persona not found")
        
        # ตรวจสอบชื่อซ้ำ (ยกเว้นตัวเอง)
        if request.name != persona.name:
            existing = db.query(ScriptPersona).filter(
                ScriptPersona.name == request.name,
                ScriptPersona.id != persona_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Script persona name '{request.name}' already exists"
                )
        
        # อัปเดตข้อมูล
        update_data = request.dict()
        for field, value in update_data.items():
            setattr(persona, field, value)
        
        db.commit()
        db.refresh(persona)
        
        print(f"✅ Updated script persona: {persona.name}")
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "update_script_persona")

@router.delete("/personas/script/{persona_id}")
async def delete_script_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    ลบ Script Persona (soft delete)
    """
    try:
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Script persona not found")
        
        persona_name = persona.name
        
        # ตรวจสอบการใช้งาน
        from ..dependencies import Script
        scripts_using = db.query(Script).filter(
            getattr(Script, 'persona_id', None) == persona_id
        ).count()
        
        if scripts_using > 0:
            # Soft delete - ปิดการใช้งานแทนการลบ
            persona.is_active = False
            db.commit()
            
            return {
                "message": f"Script persona '{persona_name}' deactivated (used by {scripts_using} scripts)",
                "success": True,
                "action": "deactivated",
                "scripts_affected": scripts_using
            }
        else:
            # Hard delete - ลบจริงเพราะไม่มีการใช้งาน
            db.delete(persona)
            db.commit()
            
            return {
                "message": f"Script persona '{persona_name}' deleted successfully",
                "success": True,
                "action": "deleted",
                "scripts_affected": 0
            }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "delete_script_persona")

# Voice Persona Endpoints
@router.get("/personas/voice")
async def get_voice_personas(
    active_only: bool = Query(True, description="แสดงเฉพาะ personas ที่ใช้งานได้"),
    provider: Optional[str] = Query(None, description="กรองตาม TTS provider"),
    language: Optional[str] = Query(None, description="กรองตามภาษา"),
    gender: Optional[str] = Query(None, description="กรองตามเพศเสียง"),
    db: Session = Depends(get_db)
):
    """
    ดึงรายการ Voice Personas พร้อมการกรอง
    """
    try:
        print("🔍 DEBUG: Starting get_voice_personas")
        query = db.query(VoicePersona)
        
        if active_only:
            query = query.filter(VoicePersona.is_active == True)
            
        if provider:
            if provider not in SUPPORTED_TTS_PROVIDERS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported provider. Valid options: {SUPPORTED_TTS_PROVIDERS}"
                )
            query = query.filter(VoicePersona.tts_provider == provider)
            
        if language:
            query = query.filter(VoicePersona.language == language)
            
        if gender:
            query = query.filter(VoicePersona.gender == gender)
        
        personas = query.order_by(asc(VoicePersona.name)).all()
        
        result = []
        for i, persona in enumerate(personas):
            try:
                print(f"🔍 DEBUG: Processing voice persona {i+1}: {persona.name}")
                persona_dict = persona.to_dict()
                
                # เพิ่มสถิติการใช้งาน
                from ..dependencies import MP3File
                mp3s_generated = db.query(MP3File).filter(
                    MP3File.voice_persona_id == persona.id
                ).count()
                
                persona_dict['mp3s_generated'] = mp3s_generated
                persona_dict['usage_count'] = getattr(persona, 'usage_count', 0)
                
                result.append(persona_dict)
                print(f"✅ DEBUG: Successfully processed voice persona {i+1}")
                
            except Exception as e:
                print(f"❌ DEBUG: Error processing voice persona {i+1} ({persona.name}): {e}")
                raise e
        
        print(f"✅ Found {len(result)} voice personas")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ ERROR in get_voice_personas: {str(e)}")
        handle_database_error(e, "get_voice_personas")

@router.post("/personas/voice", response_model=PersonaResponse)
async def create_voice_persona(
    request: VoicePersonaCreateRequest, 
    db: Session = Depends(get_db)
):
    """
    สร้าง Voice Persona ใหม่
    
    Features:
    - ตรวจสอบชื่อซ้ำ
    - ตรวจสอบ TTS provider
    - ตั้งค่าเริ่มต้น
    """
    try:
        # ตรวจสอบชื่อซ้ำ
        existing = db.query(VoicePersona).filter(VoicePersona.name == request.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Voice persona name '{request.name}' already exists"
            )
        
        # ตรวจสอบ TTS provider
        if request.tts_provider not in SUPPORTED_TTS_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported TTS provider. Valid options: {SUPPORTED_TTS_PROVIDERS}"
            )
        
        persona_data = request.dict()
        persona_data['is_active'] = True
        persona_data['usage_count'] = 0
        
        persona = VoicePersona(**persona_data)
        
        db.add(persona)
        db.commit()
        db.refresh(persona)
        
        print(f"✅ Created voice persona: {persona.name}")
        print(f"   🗣️ Provider: {request.tts_provider}")
        print(f"   🎚️ Voice ID: {request.voice_id}")
        print(f"   🌍 Language: {request.language}")
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "create_voice_persona")

@router.get("/personas/voice/{persona_id}")
async def get_voice_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    ดึงข้อมูล Voice Persona ตาม ID พร้อมสถิติการใช้งาน
    """
    try:
        persona = db.query(VoicePersona).filter(VoicePersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        persona_dict = persona.to_dict()
        
        # เพิ่มสถิติการใช้งาน
        from ..dependencies import MP3File
        mp3s_generated = db.query(MP3File).filter(
            MP3File.voice_persona_id == persona_id
        ).count()
        
        recent_usage = db.query(MP3File).filter(
            MP3File.voice_persona_id == persona_id
        ).order_by(desc(MP3File.created_at)).limit(5).all()
        
        persona_dict.update({
            'mp3s_generated': mp3s_generated,
            'usage_count': getattr(persona, 'usage_count', 0),
            'recent_usage': [
                {
                    'script_id': mp3.script_id,
                    'filename': mp3.filename,
                    'created_at': mp3.created_at.isoformat() if mp3.created_at else None
                }
                for mp3 in recent_usage
            ]
        })
        
        return persona_dict
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_voice_persona")

@router.put("/personas/voice/{persona_id}")
async def update_voice_persona(
    persona_id: int,
    request: VoicePersonaCreateRequest,
    db: Session = Depends(get_db)
):
    """
    อัปเดต Voice Persona
    """
    try:
        persona = db.query(VoicePersona).filter(VoicePersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        # ตรวจสอบชื่อซ้ำ (ยกเว้นตัวเอง)
        if request.name != persona.name:
            existing = db.query(VoicePersona).filter(
                VoicePersona.name == request.name,
                VoicePersona.id != persona_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Voice persona name '{request.name}' already exists"
                )
        
        # อัปเดตข้อมูล
        update_data = request.dict()
        for field, value in update_data.items():
            setattr(persona, field, value)
        
        db.commit()
        db.refresh(persona)
        
        print(f"✅ Updated voice persona: {persona.name}")
        
        return persona.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "update_voice_persona")

@router.delete("/personas/voice/{persona_id}")
async def delete_voice_persona(persona_id: int, db: Session = Depends(get_db)):
    """
    ลบ Voice Persona (soft delete หากมีการใช้งาน)
    """
    try:
        persona = db.query(VoicePersona).filter(VoicePersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        persona_name = persona.name
        
        # ตรวจสอบการใช้งาน
        from ..dependencies import MP3File
        mp3s_using = db.query(MP3File).filter(
            MP3File.voice_persona_id == persona_id
        ).count()
        
        if mp3s_using > 0:
            # Soft delete - ปิดการใช้งานแทนการลบ
            persona.is_active = False
            db.commit()
            
            return {
                "message": f"Voice persona '{persona_name}' deactivated (used by {mp3s_using} MP3 files)",
                "success": True,
                "action": "deactivated",
                "mp3s_affected": mp3s_using
            }
        else:
            # Hard delete - ลบจริงเพราะไม่มีการใช้งาน
            db.delete(persona)
            db.commit()
            
            return {
                "message": f"Voice persona '{persona_name}' deleted successfully",
                "success": True,
                "action": "deleted",
                "mp3s_affected": 0
            }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "delete_voice_persona")

# Utility Endpoints
@router.get("/personas/voice/providers/{provider}/voices")
async def get_provider_voices(provider: str):
    """
    ดึงรายการเสียงที่ใช้ได้สำหรับ TTS provider
    """
    try:
        if provider not in SUPPORTED_TTS_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported provider. Valid options: {SUPPORTED_TTS_PROVIDERS}"
            )
        
        # Mock data - ในการใช้งานจริงควรดึงจาก TTS service
        voice_lists = {
            "edge": [
                {"id": "th-TH-PremwadeeNeural", "name": "Premwadee (Female)", "gender": "female"},
                {"id": "th-TH-NiwatNeural", "name": "Niwat (Male)", "gender": "male"},
            ],
            "google": [
                {"id": "th-TH-Standard-A", "name": "Thai Female", "gender": "female"},
                {"id": "th-TH-Wavenet-A", "name": "Thai Female (Premium)", "gender": "female"},
            ],
            "elevenlabs": [
                {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male"},
                {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
            ]
        }
        
        return {
            "provider": provider,
            "voices": voice_lists.get(provider, []),
            "total": len(voice_lists.get(provider, []))
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_provider_voices")

@router.post("/personas/voice/{persona_id}/test")
async def test_voice_persona(
    persona_id: int,
    test_text: str = "สวัสดีครับ ทดสอบเสียงพูด",
    db: Session = Depends(get_db)
):
    """
    ทดสอบ Voice Persona ด้วยข้อความตัวอย่าง
    """
    try:
        persona = db.query(VoicePersona).filter(VoicePersona.id == persona_id).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Voice persona not found")
        
        # เรียกใช้ TTS test endpoint
        from ..dependencies import tts_service, check_tts_service_availability
        
        tts = check_tts_service_availability()
        
        # สร้าง voice config จาก persona
        voice_config = {
            "voice": persona.voice_id,
            "voice_id": persona.voice_id,
            "speed": persona.speed,
            "pitch": persona.pitch,
            "volume": persona.volume
        }
        
        # ทดสอบการสร้างเสียง
        if hasattr(tts, 'generate_emotional_speech'):
            file_path, web_url = await tts.generate_emotional_speech(
                text=test_text,
                script_id=f"test_persona_{persona_id}",
                provider=persona.tts_provider,
                voice_config=voice_config,
                emotion=getattr(persona, 'emotion', 'professional'),
                intensity=1.0,
                language=persona.language
            )
        else:
            # Fallback สำหรับ basic TTS
            file_path, web_url = await tts.generate_script_audio(
                script_id=f"test_persona_{persona_id}",
                content=test_text,
                language=persona.language,
                voice_persona=voice_config
            )
        
        if file_path and web_url:
            return {
                "success": True,
                "message": f"Voice persona '{persona.name}' test completed",
                "audio_url": web_url,
                "persona_id": persona_id,
                "test_text": test_text,
                "voice_settings": voice_config
            }
        else:
            raise HTTPException(status_code=500, detail="Voice test failed")
        
    except HTTPException:
        raise
    except Exception as e:
        handle_service_error(e, "Voice Persona Test")