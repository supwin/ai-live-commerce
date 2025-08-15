# app/services/enhanced_tts_service.py - Main Enhanced TTS Service
"""
Enhanced TTS Service - Main Entry Point
แยกย่อยแล้วเพื่อความง่ายในการบริหารจัดการ
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from .tts_config import TTSConfig, load_dependencies
from .voice_providers import VoiceProviders
from .audio_processor import AudioProcessor
from .tts_generators import (
    EdgeTTSGenerator, ElevenLabsGenerator, AzureGenerator, BasicTTSGenerator
)

class EnhancedTTSService:
    """Enhanced TTS Service with multiple providers and emotional support"""
    
    def __init__(self):
        # Initialize directories
        self.audio_dir = Path("frontend/static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = TTSConfig()
        
        # Initialize providers
        self.providers = self.config.get_provider_config()
        self._initialize_providers()
        
        print(f"🎵 Enhanced TTS Service initialized")
        available_providers = [p for p, config in self.providers.items() if config['available']]
        print(f"   📊 Available providers: {available_providers}")

    def _initialize_providers(self):
        """Initialize voice configurations for each provider"""
        try:
            if self.providers["edge"]["available"]:
                self.providers["edge"]["voices"] = VoiceProviders.get_edge_voices()
            
            if self.providers["elevenlabs"]["available"]:
                self.providers["elevenlabs"]["voices"] = VoiceProviders.get_elevenlabs_voices()
            else:
                self.providers["elevenlabs"]["voices"] = {}
            
            if self.providers["azure"]["available"]:
                self.providers["azure"]["voices"] = VoiceProviders.get_azure_voices()
            else:
                self.providers["azure"]["voices"] = {}
                
            print(f"   📊 Edge TTS voices: {len(self.providers['edge']['voices'])}")
            print(f"   🤖 ElevenLabs voices: {len(self.providers['elevenlabs']['voices'])}")
            print(f"   🏢 Azure voices: {len(self.providers['azure']['voices'])}")
            
        except Exception as e:
            print(f"⚠️ Error initializing providers: {e}")
            for provider in self.providers:
                if "voices" not in self.providers[provider]:
                    self.providers[provider]["voices"] = {}

    async def generate_emotional_speech(
        self,
        text: str,
        script_id: str,
        provider: str = "edge",
        voice_config: Optional[Dict] = None,
        emotion: str = "neutral",
        intensity: float = 1.0,
        language: str = "th",
        script_title: str = ""
    ) -> Tuple[str, str]:
        """
        สร้างเสียงพูดที่มีอารมณ์พร้อม unique filename
        """
        
        try:
            # สำหรับ test endpoint ให้ใช้ timestamp เป็น script_id
            if script_id == "test" or script_id.startswith("test"):
                import time
                unique_id = f"test_{int(time.time() * 1000)}"
            else:
                unique_id = script_id
            
            print(f"🎵 Generating speech with provider: {provider}")
            print(f"   📝 Text: {text[:50]}...")
            print(f"   🎭 Emotion: {emotion}")
            print(f"   🆔 Unique ID: {unique_id}")
            
            # เลือก provider ตามที่ระบุ
            if provider == "basic" or provider == "gtts":
                return await BasicTTSGenerator.generate(
                    text, unique_id, language, script_title, self.audio_dir
                )
            elif provider == "edge":
                return await EdgeTTSGenerator.generate(
                    text, unique_id, voice_config or {}, emotion, intensity, script_title, self.audio_dir
                )
            elif provider == "elevenlabs":
                return await ElevenLabsGenerator.generate(
                    text, unique_id, voice_config or {}, emotion, intensity, script_title, self.audio_dir
                )
            elif provider == "azure":
                return await AzureGenerator.generate(
                    text, unique_id, voice_config or {}, emotion, intensity, script_title, self.audio_dir, self.config
                )
            else:
                print(f"   ⚠️ Unknown provider '{provider}', falling back to basic")
                return await BasicTTSGenerator.generate(
                    text, unique_id, language, script_title, self.audio_dir
                )
                
        except Exception as e:
            print(f"❌ Error generating speech with {provider}: {e}")
            # Fallback to basic TTS
            try:
                print(f"   🔄 Falling back to basic TTS")
                return await BasicTTSGenerator.generate(
                    text, unique_id, language, script_title, self.audio_dir
                )
            except Exception as fallback_error:
                print(f"❌ Even basic TTS failed: {fallback_error}")
                return "", ""
    
    def _get_best_available_provider(self) -> str:
        """เลือก provider ที่ดีที่สุดที่มีอยู่"""
        try:
            # ลำดับความต้องการ: edge > elevenlabs > azure > basic
            priority_order = ["edge", "elevenlabs", "azure", "basic"]
            
            for provider in priority_order:
                if (provider in self.providers and 
                    self.providers[provider].get("available", False)):
                    print(f"   🎯 Selected provider: {provider}")
                    return provider
            
            # หาก providers ไม่มีเลย ให้ใช้ basic
            print("   ⚠️ No enhanced providers available, using basic fallback")
            return "basic"
            
        except Exception as e:
            print(f"   ❌ Error selecting provider: {e}")
            return "basic"
    
    def is_enhanced_available(self) -> bool:
        """ตรวจสอบว่า Enhanced TTS พร้อมใช้งานหรือไม่"""
        enhanced_providers = ["edge", "elevenlabs", "azure"]
        return any(self.providers.get(p, {}).get("available", False) for p in enhanced_providers)

    def get_recommended_provider(self) -> str:
        """แนะนำ provider ที่เหมาะสม"""
        if self.providers.get("edge", {}).get("available", False):
            return "edge"
        elif self.providers.get("elevenlabs", {}).get("available", False):
            return "elevenlabs"
        elif self.providers.get("azure", {}).get("available", False):
            return "azure"
        else:
            return "basic"

    def get_provider_status(self) -> Dict[str, Any]:
        """สถานะของ providers ทั้งหมด"""
        status = {}
        for provider, config in self.providers.items():
            status[provider] = {
                "available": config.get("available", False),
                "quality": config.get("quality", "unknown"),
                "cost": config.get("cost", "unknown"),
                "voice_count": len(config.get("voices", {})),
                "supports_emotions": config.get("supports_emotions", False)
            }
        return status

    # เมธอดสำหรับ compatibility กับระบบเดิม
    async def generate_script_audio(
        self,
        script_id: str,
        content: str,
        language: str = "th",
        voice_persona: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """Generate audio for script - compatible with existing system แก้ไขแล้ว"""
        
        try:
            print(f"🎵 Generating audio for script {script_id}")
            
            # Parse voice persona config safely
            script_title = f"Script {script_id}"  # Default title
            if voice_persona:
                provider = voice_persona.get("tts_provider", "edge")
                emotion = voice_persona.get("emotion", "professional")
                voice_config = {
                    "voice": voice_persona.get("voice_id", "th-TH-PremwadeeNeural"),
                    "voice_id": voice_persona.get("voice_id", "pNInz6obpgDQGcFmaJgB")
                }
                intensity = voice_persona.get("emotional_intensity", 1.0)
                # ดึง script title จาก voice_persona หากมี
                script_title = voice_persona.get("script_title", script_title)
            else:
                provider = self.get_recommended_provider()
                emotion = "professional"
                voice_config = {"voice": "th-TH-PremwadeeNeural"}
                intensity = 1.0
            
            print(f"   🎭 Using provider: {provider}")
            print(f"   🗣️ Voice config: {voice_config}")
            print(f"   🎭 Emotion: {emotion}")
            print(f"   🏷️ Title: {script_title}")
            
            # ตรวจสอบว่า provider พร้อมใช้งาน
            if not self.providers.get(provider, {}).get("available", False):
                print(f"   ⚠️ Provider {provider} not available, switching to best available")
                provider = self._get_best_available_provider()
            
            # ใช้ enhanced generation หากมี
            if provider != "basic":
                return await self.generate_emotional_speech(
                    text=content,
                    script_id=script_id,
                    provider=provider,
                    voice_config=voice_config,
                    emotion=emotion,
                    intensity=intensity,
                    language=language,
                    script_title=script_title  # ส่ง title ไปด้วย
                )
            else:
                # ใช้ basic fallback
                print(f"   📢 Using basic fallback for {provider}")
                return await BasicTTSGenerator.generate(
                    content, script_id, language, script_title, self.audio_dir
                )
                
        except Exception as e:
            print(f"❌ Error in generate_script_audio: {e}")
            # Ultimate fallback
            try:
                return await BasicTTSGenerator.generate(
                    content, script_id, language, "Script Audio", self.audio_dir
                )
            except Exception as fallback_error:
                print(f"❌ Even fallback failed: {fallback_error}")
                return "", ""
    
    def get_available_providers(self) -> Dict[str, Any]:
        """รายการ providers ที่ใช้ได้"""
        return {
            provider: {
                "available": config["available"],
                "voices": config["voices"],
                "supports_emotions": config["supports_emotions"],
                "quality": config["quality"],
                "cost": config["cost"]
            }
            for provider, config in self.providers.items()
        }
    
    def get_emotions_for_provider(self, provider: str) -> list:
        """รายการอารมณ์ที่ provider รองรับ"""
        return VoiceProviders.get_emotions_for_provider(provider)

# สร้าง global instance
enhanced_tts_service = EnhancedTTSService()