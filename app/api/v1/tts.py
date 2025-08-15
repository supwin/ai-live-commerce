from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from app.services.tts import enhanced_tts_service
from app.core.config import get_settings

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: str = "th-TH-PremwadeeNeural"
    language: str = "th"
    emotion: str = "professional"
    intensity: float = 1.0
    provider: str = "edge"
    script_title: Optional[str] = None

class VoicePersona(BaseModel):
    name: str
    voice_id: str
    emotion: str = "professional"
    emotional_intensity: float = 1.0
    tts_provider: str = "edge"
    language: str = "th"

@router.post("/tts/generate")
async def generate_tts(request: TTSRequest):
    """Generate high-quality Thai TTS with emotions"""
    try:
        print(f"🎤 TTS Request: {request.text[:50]}... ({request.emotion})")
        
        # Create unique script ID for this request
        import time
        script_id = f"tts_{int(time.time() * 1000)}"
        
        # Prepare voice configuration
        voice_config = {
            "voice": request.voice,
            "voice_id": request.voice if "Neural" in request.voice else "th-TH-PremwadeeNeural"
        }
        
        # Generate speech with enhanced service
        file_path, web_url = await enhanced_tts_service.generate_emotional_speech(
            text=request.text,
            script_id=script_id,
            provider=request.provider,
            voice_config=voice_config,
            emotion=request.emotion,
            intensity=request.intensity,
            language=request.language,
            script_title=request.script_title or "TTS Generated Audio"
        )
        
        if file_path and web_url:
            return {
                "status": "completed",
                "audio_url": web_url,
                "file_path": file_path,
                "text": request.text,
                "voice": request.voice,
                "emotion": request.emotion,
                "provider": request.provider,
                "language": request.language,
                "script_id": script_id
            }
        else:
            raise HTTPException(status_code=500, detail="TTS generation failed")
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating TTS: {str(e)}")

@router.get("/tts/voices")
async def get_voices():
    """Get available TTS voices with emotions"""
    try:
        providers = enhanced_tts_service.get_available_providers()
        
        all_voices = []
        for provider_name, provider_config in providers.items():
            if provider_config['available']:
                for voice_id, voice_data in provider_config['voices'].items():
                    all_voices.append({
                        "id": voice_id,
                        "name": voice_data.get('name', voice_id),
                        "provider": provider_name,
                        "language": voice_data.get('language', 'th'),
                        "gender": voice_data.get('gender', 'unknown'),
                        "emotions": voice_data.get('emotions', []),
                        "quality": provider_config['quality'],
                        "cost": provider_config['cost']
                    })
        
        return {
            "voices": all_voices,
            "providers": enhanced_tts_service.get_provider_status(),
            "recommended_provider": enhanced_tts_service.get_recommended_provider()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voices: {str(e)}")

@router.get("/tts/emotions/{provider}")
async def get_emotions(provider: str):
    """Get available emotions for a provider"""
    try:
        emotions = enhanced_tts_service.get_emotions_for_provider(provider)
        return {
            "provider": provider,
            "emotions": emotions,
            "descriptions": {
                "cheerful": "เสียงร่าเริงและมีความสุข",
                "excited": "เสียงตื่นเต้นและกระตือรือร้น", 
                "professional": "เสียงมืออาชีพและเป็นทางการ",
                "friendly": "เสียงเป็นมิตรและอบอุ่น",
                "confident": "เสียงมั่นใจและแน่วแน่",
                "calm": "เสียงสงบและผ่อนคลาย",
                "energetic": "เสียงมีพลังและกระปรี้กระเปร่า",
                "serious": "เสียงจริงจังและเคร่งขรึม",
                "gentle": "เสียงอ่อนโยนและนุ่มนวล"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting emotions: {str(e)}")

@router.post("/tts/test")
async def test_tts():
    """Test TTS system with sample Thai text"""
    try:
        test_text = "สวัสดีครับ ยินดีต้อนรับสู่ระบบ AI Live Commerce ที่จะช่วยให้การขายสินค้าของคุณมีประสิทธิภาพมากขึ้น"
        
        # Test with different emotions
        test_results = []
        test_emotions = ["professional", "cheerful", "friendly", "confident"]
        
        provider = enhanced_tts_service.get_recommended_provider()
        
        for emotion in test_emotions:
            try:
                script_id = f"test_{emotion}_{int(time.time())}"
                
                file_path, web_url = await enhanced_tts_service.generate_emotional_speech(
                    text=test_text,
                    script_id=script_id,
                    provider=provider,
                    voice_config={"voice": "th-TH-PremwadeeNeural"},
                    emotion=emotion,
                    intensity=1.2,
                    language="th",
                    script_title=f"Test Audio - {emotion}"
                )
                
                test_results.append({
                    "emotion": emotion,
                    "status": "success" if file_path else "failed",
                    "audio_url": web_url if web_url else None,
                    "provider": provider
                })
                
            except Exception as e:
                test_results.append({
                    "emotion": emotion,
                    "status": "failed",
                    "error": str(e),
                    "provider": provider
                })
        
        return {
            "test_text": test_text,
            "provider_used": provider,
            "results": test_results,
            "system_status": enhanced_tts_service.get_provider_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS test failed: {str(e)}")

@router.get("/tts/status")
async def get_tts_status():
    """Get comprehensive TTS system status"""
    try:
        return {
            "enhanced_available": enhanced_tts_service.is_enhanced_available(),
            "recommended_provider": enhanced_tts_service.get_recommended_provider(),
            "providers": enhanced_tts_service.get_provider_status(),
            "available_providers": enhanced_tts_service.get_available_providers(),
            "settings": get_settings().get_tts_config()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting TTS status: {str(e)}")