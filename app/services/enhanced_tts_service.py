# ใน app/services/enhanced_tts_service.py

import os
import asyncio
import aiofiles
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import hashlib
import json
from datetime import datetime

# Safe TTS Providers Import
EDGE_TTS_AVAILABLE = False
ELEVENLABS_AVAILABLE = False
AZURE_AVAILABLE = False
AUDIO_PROCESSING_AVAILABLE = False

# Edge TTS
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
    print("✅ Edge TTS library loaded")
except ImportError as e:
    print(f"⚠️ Edge TTS not available: {e}")

# ElevenLabs
try:
    from elevenlabs import generate, set_api_key, voices
    ELEVENLABS_AVAILABLE = True
    print("✅ ElevenLabs library loaded")
except ImportError as e:
    print(f"⚠️ ElevenLabs not available: {e}")

# Azure Speech
try:
    import azure.cognitiveservices.speech as speechsdk
    AZURE_AVAILABLE = True
    print("✅ Azure Speech library loaded")
except ImportError as e:
    print(f"⚠️ Azure Speech not available: {e}")

# Audio processing
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    AUDIO_PROCESSING_AVAILABLE = True
    print("✅ Audio processing libraries loaded")
except ImportError as e:
    print(f"⚠️ Audio processing not available: {e}")

# Basic gTTS fallback
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
    print("✅ Basic gTTS loaded as fallback")
except ImportError as e:
    print(f"❌ gTTS not available: {e}")
    GTTS_AVAILABLE = False

class EnhancedTTSService:
    """Enhanced TTS Service with multiple providers and emotional support"""
    
    def __init__(self):
        self.audio_dir = Path("frontend/static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize API keys as None first
        self.elevenlabs_api_key = None
        self.azure_speech_key = None
        self.azure_speech_region = "southeastasia"
        
        # Provider configurations - initialize before loading API keys
        self.providers = {
            "edge": {
                "available": EDGE_TTS_AVAILABLE,
                "voices": {},
                "supports_emotions": True,
                "quality": "high",
                "cost": "free"
            },
            "elevenlabs": {
                "available": ELEVENLABS_AVAILABLE,
                "voices": {},
                "supports_emotions": True,
                "quality": "premium",
                "cost": "paid"
            },
            "azure": {
                "available": AZURE_AVAILABLE,
                "voices": {},
                "supports_emotions": True,
                "quality": "enterprise",
                "cost": "paid"
            }
        }
        
        # Load API keys and initialize providers
        self._load_api_keys()
        self._initialize_providers()
        
        print(f"🎵 Enhanced TTS Service initialized")
        available_providers = [p for p, config in self.providers.items() if config['available']]
        print(f"   📊 Available providers: {available_providers}")

    def _load_api_keys(self):
        """โหลด API keys จาก environment variables - แก้ไขแล้ว"""
        try:
            self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
            self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION", "southeastasia")
            
            # Configure ElevenLabs if available
            if self.elevenlabs_api_key and ELEVENLABS_AVAILABLE:
                try:
                    set_api_key(self.elevenlabs_api_key)
                    print("✅ ElevenLabs API key configured")
                    self.providers["elevenlabs"]["available"] = True
                except Exception as e:
                    print(f"⚠️ ElevenLabs configuration failed: {e}")
                    self.providers["elevenlabs"]["available"] = False
            else:
                if not self.elevenlabs_api_key:
                    print("ℹ️ ElevenLabs API key not found (optional)")
                self.providers["elevenlabs"]["available"] = False
            
            # Configure Azure if available
            if self.azure_speech_key and AZURE_AVAILABLE:
                print("✅ Azure Speech API key configured")
                self.providers["azure"]["available"] = True
            else:
                if not self.azure_speech_key:
                    print("ℹ️ Azure Speech API key not found (optional)")
                self.providers["azure"]["available"] = False
                
        except Exception as e:
            print(f"⚠️ Error loading API keys: {e}")
            # Set safe defaults
            self.elevenlabs_api_key = None
            self.azure_speech_key = None
            self.providers["elevenlabs"]["available"] = False
            self.providers["azure"]["available"] = False

    def _initialize_providers(self):
        """Initialize voice configurations for each provider"""
        try:
            # Initialize Edge TTS voices
            if self.providers["edge"]["available"]:
                self.providers["edge"]["voices"] = self._get_edge_voices()
            
            # Initialize ElevenLabs voices  
            if self.providers["elevenlabs"]["available"]:
                self.providers["elevenlabs"]["voices"] = self._get_elevenlabs_voices()
            else:
                self.providers["elevenlabs"]["voices"] = {}
            
            # Initialize Azure voices
            if self.providers["azure"]["available"]:
                self.providers["azure"]["voices"] = self._get_azure_voices()
            else:
                self.providers["azure"]["voices"] = {}
                
            print(f"   🔊 Edge TTS voices: {len(self.providers['edge']['voices'])}")
            print(f"   🤖 ElevenLabs voices: {len(self.providers['elevenlabs']['voices'])}")
            print(f"   🏢 Azure voices: {len(self.providers['azure']['voices'])}")
            
        except Exception as e:
            print(f"⚠️ Error initializing providers: {e}")
            # Set safe defaults
            for provider in self.providers:
                if "voices" not in self.providers[provider]:
                    self.providers[provider]["voices"] = {}
    
    def _get_edge_voices(self) -> Dict[str, Any]:
        """รายการ Edge TTS voices ที่รองรับอารมณ์"""
        return {
            "th_female_professional": {
                "voice": "th-TH-PremwadeeNeural",
                "name": "Premwadee (Thai Female Professional)",
                "language": "th-TH",
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
            },
            "th_male_casual": {
                "voice": "th-TH-NiwatNeural", 
                "name": "Niwat (Thai Male Casual)",
                "language": "th-TH",
                "gender": "male",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious"]
            },
            "th_female_warm": {
                "voice": "th-TH-AcharaNeural",
                "name": "Achara (Thai Female Warm)",
                "language": "th-TH", 
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle"]
            },
            "en_female_professional": {
                "voice": "en-US-JennyNeural",
                "name": "Jenny (English Female Professional)",
                "language": "en-US",
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
            }
        }
    
    def _get_elevenlabs_voices(self) -> Dict[str, Any]:
        """รายการ ElevenLabs voices (จะโหลดจาก API หากมี key) - แก้ไขแล้ว"""
        try:
            # ตรวจสอบว่ามี API key และ service พร้อมใช้งาน
            if not hasattr(self, 'elevenlabs_api_key') or not self.elevenlabs_api_key:
                print("ℹ️ ElevenLabs API key not configured")
                return {}
            
            if not ELEVENLABS_AVAILABLE:
                print("ℹ️ ElevenLabs library not available")
                return {}
            
            # ใช้ static voices แทนการเรียก API (เพื่อความเสถียร)
            return {
                "adam": {
                    "voice_id": "pNInz6obpgDQGcFmaJgB",
                    "name": "Adam (English Male)",
                    "language": "en",
                    "gender": "male",
                    "emotions": ["neutral", "excited", "sad", "angry", "cheerful", "serious"]
                },
                "bella": {
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",
                    "name": "Bella (English Female)",
                    "language": "en", 
                    "gender": "female",
                    "emotions": ["neutral", "excited", "sad", "angry", "cheerful", "serious", "gentle"]
                },
                "rachel": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "name": "Rachel (English Female Professional)",
                    "language": "en",
                    "gender": "female", 
                    "emotions": ["neutral", "professional", "confident", "cheerful", "serious"]
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error getting ElevenLabs voices: {e}")
            return {}
    
    def _get_azure_voices(self) -> Dict[str, Any]:
        """รายการ Azure Speech voices - แก้ไขแล้ว"""
        try:
            # ตรวจสอบว่ามี API key และ service พร้อมใช้งาน  
            if not hasattr(self, 'azure_speech_key') or not self.azure_speech_key:
                print("ℹ️ Azure Speech API key not configured")
                return {}
                
            if not AZURE_AVAILABLE:
                print("ℹ️ Azure Speech library not available")
                return {}
                
            return {
                "th_female_premium": {
                    "voice": "th-TH-PremwadeeNeural",
                    "name": "Premwadee Premium (Azure)",
                    "language": "th-TH",
                    "gender": "female", 
                    "emotions": ["cheerful", "sad", "angry", "fearful", "serious", "gentle"]
                },
                "th_male_premium": {
                    "voice": "th-TH-NiwatNeural",
                    "name": "Niwat Premium (Azure)",
                    "language": "th-TH",
                    "gender": "male",
                    "emotions": ["cheerful", "sad", "angry", "fearful", "serious"]
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error getting Azure voices: {e}")
            return {}
    
    async def generate_emotional_speech(
        self,
        text: str,
        script_id: str,
        provider: str = "edge",
        voice_config: Optional[Dict] = None,
        emotion: str = "neutral",
        intensity: float = 1.0,
        language: str = "th"
    ) -> Tuple[str, str]:
        """
        สร้างเสียงพูดที่มีอารมณ์
        
        Args:
            text: ข้อความที่จะแปลงเป็นเสียง
            script_id: ID ของสคริปต์
            provider: ผู้ให้บริการ TTS (edge, elevenlabs, azure)
            voice_config: การตั้งค่าเสียง
            emotion: อารมณ์ (cheerful, sad, angry, etc.)
            intensity: ความเข้มของอารมณ์ (0.0-2.0)
            language: ภาษา
            
        Returns:
            tuple: (file_path, web_url)
        """
        
        try:
            # เลือก provider ที่เหมาะสม
            if provider not in self.providers or not self.providers[provider]["available"]:
                provider = self._get_best_available_provider()
                
            print(f"🎵 Generating emotional speech:")
            print(f"   📝 Text: {text[:50]}...")
            print(f"   🎭 Emotion: {emotion} (intensity: {intensity})")
            print(f"   🔊 Provider: {provider}")
            print(f"   🗣️ Voice: {voice_config}")
            
            # สร้างไฟล์ audio ตาม provider
            if provider == "edge":
                return await self._generate_edge_speech(text, script_id, voice_config, emotion, intensity)
            elif provider == "elevenlabs":
                return await self._generate_elevenlabs_speech(text, script_id, voice_config, emotion, intensity)
            elif provider == "azure":
                return await self._generate_azure_speech(text, script_id, voice_config, emotion, intensity)
            else:
                # Fallback to basic gTTS
                return await self._generate_basic_speech(text, script_id, language)
                
        except Exception as e:
            print(f"❌ Error generating emotional speech: {e}")
            # Fallback to basic TTS
            return await self._generate_basic_speech(text, script_id, language)
    
    async def _generate_edge_speech(
        self, 
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย Edge TTS พร้อมอารมณ์"""
        
        try:
            # เลือกเสียงจาก voice_config หรือใช้ default
            voice_name = voice_config.get("voice", "th-TH-PremwadeeNeural")
            
            # สร้าง SSML พร้อมอารมณ์
            ssml_text = self._create_emotional_ssml(text, voice_name, emotion, intensity)
            
            # กำหนดเส้นทางไฟล์
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   🎭 Using SSML with emotion: {emotion}")
            print(f"   📁 Output: {file_path}")
            
            # สร้าง TTS
            communicate = edge_tts.Communicate(ssml_text, voice_name)
            await communicate.save(str(file_path))
            
            # ปรับปรุงคุณภาพเสียง
            if AUDIO_PROCESSING_AVAILABLE:
                await self._enhance_audio_quality(file_path)
            
            print(f"   ✅ Edge TTS generation completed")
            return str(file_path), web_url
            
        except Exception as e:
            print(f"   ❌ Edge TTS failed: {e}")
            raise
    
    async def _generate_elevenlabs_speech(
        self, 
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย ElevenLabs AI"""
        
        try:
            voice_id = voice_config.get("voice_id", "pNInz6obpgDQGcFmaJgB")
            
            # ปรับ text สำหรับอารมณ์
            emotional_text = self._add_emotional_context(text, emotion, intensity)
            
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   🤖 Using ElevenLabs voice: {voice_id}")
            print(f"   📁 Output: {file_path}")
            
            # สร้าง audio
            audio = generate(
                text=emotional_text,
                voice=voice_id,
                model="eleven_multilingual_v2"
            )
            
            # บันทึกไฟล์
            with open(file_path, "wb") as f:
                f.write(audio)
            
            print(f"   ✅ ElevenLabs generation completed")
            return str(file_path), web_url
            
        except Exception as e:
            print(f"   ❌ ElevenLabs failed: {e}")
            raise
    
    async def _generate_azure_speech(
        self, 
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย Azure Cognitive Services"""
        
        try:
            # สร้าง Azure Speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key, 
                region=self.azure_speech_region
            )
            
            voice_name = voice_config.get("voice", "th-TH-PremwadeeNeural")
            speech_config.speech_synthesis_voice_name = voice_name
            
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.wav"
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            # สร้าง SSML พร้อมอารมณ์
            ssml_text = self._create_emotional_ssml(text, voice_name, emotion, intensity)
            
            # สร้าง synthesizer
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(file_path))
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            # สังเคราะห์เสียง
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # แปลงเป็น MP3
                mp3_path = await self._convert_to_mp3(file_path)
                print(f"   ✅ Azure Speech generation completed")
                return str(mp3_path), web_url.replace('.wav', '.mp3')
            else:
                raise Exception(f"Azure synthesis failed: {result.reason}")
                
        except Exception as e:
            print(f"   ❌ Azure Speech failed: {e}")
            raise
    
    def _create_emotional_ssml(self, text: str, voice_name: str, emotion: str, intensity: float) -> str:
        """สร้าง SSML ที่รองรับอารมณ์"""
        
        # แปลงอารมณ์ให้เหมาะสมกับ SSML
        emotion_mapping = {
            "excited": "cheerful",
            "happy": "cheerful", 
            "professional": "serious",
            "friendly": "gentle",
            "confident": "serious",
            "energetic": "cheerful",
            "calm": "gentle",
            "urgent": "angry"
        }
        
        ssml_emotion = emotion_mapping.get(emotion, emotion)
        
        # ปรับ intensity
        intensity_level = "strong" if intensity > 1.5 else "moderate" if intensity > 1.0 else "mild"
        
        # สร้าง SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
            <voice name="{voice_name}">
                <mstts:express-as style="{ssml_emotion}" styledegree="{intensity}">
                    <prosody rate="{self._get_prosody_rate(emotion)}" pitch="{self._get_prosody_pitch(emotion)}">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        return ssml.strip()
    
    def _get_prosody_rate(self, emotion: str) -> str:
        """กำหนดอัตราการพูดตามอารมณ์"""
        rates = {
            "excited": "+20%",
            "energetic": "+15%", 
            "urgent": "+25%",
            "calm": "-10%",
            "professional": "+5%",
            "friendly": "+10%"
        }
        return rates.get(emotion, "medium")
    
    def _get_prosody_pitch(self, emotion: str) -> str:
        """กำหนดระดับเสียงตามอารมณ์"""
        pitches = {
            "excited": "+15%",
            "happy": "+10%",
            "energetic": "+12%",
            "sad": "-15%",
            "calm": "-5%",
            "professional": "medium",
            "confident": "+8%"
        }
        return pitches.get(emotion, "medium")
    
    def _add_emotional_context(self, text: str, emotion: str, intensity: float) -> str:
        """เพิ่ม emotional context ให้กับข้อความสำหรับ AI voices"""
        
        emotion_prefixes = {
            "excited": "ด้วยความตื่นเต้นและกระตือรือร้น: ",
            "happy": "ด้วยความสุขและความยินดี: ",
            "professional": "ด้วยมาตรฐานทางวิชาชีพ: ",
            "friendly": "ด้วยความเป็นมิตรและอบอุ่น: ",
            "confident": "ด้วยความมั่นใจและแน่วแน่: ",
            "energetic": "ด้วยพลังและความกระปรี้กระเปร่า: ",
            "calm": "ด้วยความสงบและใจเย็น: ",
            "urgent": "ด้วยความเร่งด่วนและจำกัดเวลา: "
        }
        
        prefix = emotion_prefixes.get(emotion, "")
        return f"{prefix}{text}" if prefix else text
    
    async def _enhance_audio_quality(self, file_path: Path):
        """ปรับปรุงคุณภาพเสียง"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return
                
            # โหลดและปรับปรุงเสียง
            audio = AudioSegment.from_file(file_path)
            
            # Normalize volume
            audio = normalize(audio)
            
            # Compress dynamic range เล็กน้อย
            audio = compress_dynamic_range(audio)
            
            # ปรับ sample rate สำหรับคุณภาพที่ดี
            audio = audio.set_frame_rate(22050)
            
            # บันทึกกลับ
            audio.export(file_path, format="mp3", bitrate="128k")
            
            print(f"   🎧 Audio quality enhanced")
            
        except Exception as e:
            print(f"   ⚠️ Audio enhancement failed: {e}")
    
    async def _convert_to_mp3(self, wav_path: Path) -> Path:
        """แปลงไฟล์ WAV เป็น MP3"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return wav_path
                
            mp3_path = wav_path.with_suffix('.mp3')
            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3", bitrate="128k")
            
            # ลบไฟล์ WAV
            if wav_path.exists():
                wav_path.unlink()
                
            return mp3_path
            
        except Exception as e:
            print(f"   ⚠️ MP3 conversion failed: {e}")
            return wav_path
    
    def _get_best_available_provider(self) -> str:
        """เลือก provider ที่ดีที่สุดที่มีอยู่ - แก้ไขแล้ว"""
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
    
    async def _generate_basic_speech(self, text: str, script_id: str, language: str = "th") -> Tuple[str, str]:
        """Fallback เป็น basic gTTS - แก้ไขแล้ว"""
        try:
            if not GTTS_AVAILABLE:
                print("   ❌ gTTS not available for fallback")
                return "", ""
            
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   📢 Using basic gTTS fallback")
            print(f"   📁 Output: {file_path}")
            
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(file_path))
            
            print(f"   ✅ Basic gTTS generation completed")
            return str(file_path), web_url
            
        except Exception as e:
            print(f"   ❌ Basic TTS failed: {e}")
            return "", ""
    
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
            if voice_persona:
                provider = voice_persona.get("tts_provider", "edge")
                emotion = voice_persona.get("emotion", "professional")
                voice_config = {
                    "voice": voice_persona.get("voice_id", "th-TH-PremwadeeNeural"),
                    "voice_id": voice_persona.get("voice_id", "pNInz6obpgDQGcFmaJgB")
                }
                intensity = voice_persona.get("emotional_intensity", 1.0)
            else:
                provider = self.get_recommended_provider()
                emotion = "professional"
                voice_config = {"voice": "th-TH-PremwadeeNeural"}
                intensity = 1.0
            
            print(f"   🎭 Using provider: {provider}")
            print(f"   🗣️ Voice config: {voice_config}")
            print(f"   🎭 Emotion: {emotion}")
            
            # ตรวจสอบว่า provider พร้อมใช้งาน
            if not self.providers.get(provider, {}).get("available", False):
                print(f"   ⚠️ Provider {provider} not available, switching to best available")
                provider = self._get_best_available_provider()
            
            # ใช้ enhanced generation หากมี
            if hasattr(self, 'generate_emotional_speech') and provider != "basic":
                return await self.generate_emotional_speech(
                    text=content,
                    script_id=script_id,
                    provider=provider,
                    voice_config=voice_config,
                    emotion=emotion,
                    intensity=intensity,
                    language=language
                )
            else:
                # ใช้ basic fallback
                print(f"   📢 Using basic fallback for {provider}")
                return await self._generate_basic_speech(content, script_id, language)
                
        except Exception as e:
            print(f"❌ Error in generate_script_audio: {e}")
            # Ultimate fallback
            try:
                return await self._generate_basic_speech(content, script_id, language)
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
        if provider == "edge":
            return ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
        elif provider == "elevenlabs":
            return ["neutral", "excited", "sad", "angry", "cheerful", "serious", "gentle"]
        elif provider == "azure":
            return ["cheerful", "sad", "angry", "fearful", "serious", "gentle"]
        else:
            return ["neutral"]

# สร้าง global instance
enhanced_tts_service = EnhancedTTSService()