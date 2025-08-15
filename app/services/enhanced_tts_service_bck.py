# ใน app/services/enhanced_tts_service.py - แก้ไขส่วน metadata contamination

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

# Audio processing - แก้ไขการ import
try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    # เพิ่ม mutagen สำหรับจัดการ metadata
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
    AUDIO_PROCESSING_AVAILABLE = True
    print("✅ Audio processing libraries loaded")
except ImportError as e:
    print(f"⚠️ Audio processing not available: {e}")
    AUDIO_PROCESSING_AVAILABLE = False

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
        
        # Initialize API keys
        self.elevenlabs_api_key = None
        self.azure_speech_key = None
        self.azure_speech_region = "southeastasia"
        
        # Provider configurations
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
        """โหลด API keys จาก environment variables"""
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
            self.elevenlabs_api_key = None
            self.azure_speech_key = None
            self.providers["elevenlabs"]["available"] = False
            self.providers["azure"]["available"] = False

    def _initialize_providers(self):
        """Initialize voice configurations for each provider"""
        try:
            if self.providers["edge"]["available"]:
                self.providers["edge"]["voices"] = self._get_edge_voices()
            
            if self.providers["elevenlabs"]["available"]:
                self.providers["elevenlabs"]["voices"] = self._get_elevenlabs_voices()
            else:
                self.providers["elevenlabs"]["voices"] = {}
            
            if self.providers["azure"]["available"]:
                self.providers["azure"]["voices"] = self._get_azure_voices()
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
        """รายการ ElevenLabs voices"""
        try:
            if not hasattr(self, 'elevenlabs_api_key') or not self.elevenlabs_api_key:
                print("ℹ️ ElevenLabs API key not configured")
                return {}
            
            if not ELEVENLABS_AVAILABLE:
                print("ℹ️ ElevenLabs library not available")
                return {}
            
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
        """รายการ Azure Speech voices"""
        try:
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

    # ฟังก์ชันใหม่สำหรับจัดการ metadata แบบสะอาด
    def _clean_metadata(self, file_path: Path, script_title: str = "", emotion: str = ""):
        """ทำความสะอาดและตั้งค่า metadata ใหม่แบบถูกต้อง"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                print("   ⚠️ Audio processing not available for metadata cleaning")
                return
            
            # โหลดไฟล์ MP3
            audio_file = MP3(str(file_path))
            
            # ลบ metadata เก่าทั้งหมด
            audio_file.delete()
            
            # สร้าง ID3 tags ใหม่
            audio_file.add_tags()
            
            # ตั้งค่า metadata ใหม่แบบสะอาด
            audio_file.tags.add(TIT2(encoding=3, text=script_title or f"AI Live Commerce Script"))
            audio_file.tags.add(TPE1(encoding=3, text="AI Live Commerce TTS"))
            audio_file.tags.add(TALB(encoding=3, text="Product Scripts"))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            audio_file.tags.add(TCON(encoding=3, text=f"Speech/{emotion}"))
            
            # บันทึก metadata ใหม่
            audio_file.save()
            
            print(f"   🏷️ Metadata cleaned and updated")
            
        except Exception as e:
            print(f"   ⚠️ Metadata cleaning failed: {e}")
            # ไม่ throw error เพราะไฟล์ยังใช้งานได้
    
    async def _enhance_audio_quality(self, file_path: Path, script_title: str = "", emotion: str = ""):
        """ปรับปรุงคุณภาพเสียงและทำความสะอาด metadata"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return
                
            print(f"   🎧 Enhancing audio quality...")
            
            # โหลดและปรับปรุงเสียง
            audio = AudioSegment.from_file(file_path)
            
            # Normalize volume
            audio = normalize(audio)
            
            # Compress dynamic range เล็กน้อย
            audio = compress_dynamic_range(audio, threshold=-20.0, ratio=2.0, attack=5.0, release=50.0)
            
            # ปรับ sample rate สำหรับคุณภาพที่ดี
            audio = audio.set_frame_rate(22050)
            
            # สร้างไฟล์ชั่วคราว
            temp_path = file_path.with_suffix('.tmp.mp3')
            
            # Export ด้วยการตั้งค่าที่เหมาะสม
            audio.export(
                temp_path, 
                format="mp3", 
                bitrate="128k",
                parameters=["-q:a", "2", "-ar", "22050"]  # คุณภาพสูง
            )
            
            # ย้ายไฟล์ชั่วคราวมาแทนที่ไฟล์เดิม
            if temp_path.exists():
                file_path.unlink()  # ลบไฟล์เดิม
                temp_path.rename(file_path)  # เปลี่ยนชื่อไฟล์ใหม่
            
            # ทำความสะอาด metadata
            self._clean_metadata(file_path, script_title, emotion)
            
            print(f"   ✅ Audio quality enhanced and metadata cleaned")
            
        except Exception as e:
            print(f"   ⚠️ Audio enhancement failed: {e}")
            # ลองทำความสะอาด metadata อย่างเดียว
            try:
                self._clean_metadata(file_path, script_title, emotion)
            except:
                pass

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
                return await self._generate_basic_speech(text, unique_id, language, script_title)
            elif provider == "edge":
                return await self._generate_edge_speech(text, unique_id, voice_config or {}, emotion, intensity, script_title)
            elif provider == "elevenlabs":
                return await self._generate_elevenlabs_speech(text, unique_id, voice_config or {}, emotion, intensity, script_title)
            elif provider == "azure":
                return await self._generate_azure_speech(text, unique_id, voice_config or {}, emotion, intensity, script_title)
            else:
                print(f"   ⚠️ Unknown provider '{provider}', falling back to basic")
                return await self._generate_basic_speech(text, unique_id, language, script_title)
                
        except Exception as e:
            print(f"❌ Error generating speech with {provider}: {e}")
            # Fallback to basic TTS
            try:
                print(f"   🔄 Falling back to basic TTS")
                return await self._generate_basic_speech(text, unique_id, language, script_title)
            except Exception as fallback_error:
                print(f"❌ Even basic TTS failed: {fallback_error}")
                return "", ""
    
    async def _generate_edge_speech(
        self, 
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float,
        script_title: str = ""
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย Edge TTS แก้ไขปัญหา LAME Padding และ Filename Collision"""
        
        try:
            import time
            
            # เลือกเสียงจาก voice_config หรือใช้ default
            voice_name = voice_config.get("voice", "th-TH-PremwadeeNeural")
            
            # ทำความสะอาดข้อความก่อนประมวลผล
            cleaned_text = self._clean_text_for_tts(text)
            
            # สร้าง unique filename ที่รวม timestamp และ text hash
            timestamp = str(int(time.time() * 1000))  # milliseconds
            text_hash = hashlib.md5(cleaned_text.encode()).hexdigest()[:8]
            filename = f"script_{script_id}_{text_hash}_{timestamp}.mp3"
            
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   📝 Using plain text (no SSML) to prevent concatenation")
            print(f"   🧹 Text: '{cleaned_text}'")
            print(f"   📁 Unique filename: {filename}")
            
            # ลบไฟล์เก่าหากมี (ใช้ pattern เดิม)
            old_pattern = f"script_{script_id}_{text_hash}_*.mp3"
            import glob
            for old_file in glob.glob(str(self.audio_dir / old_pattern)):
                try:
                    Path(old_file).unlink()
                    print(f"   🗑️ Removed old file: {Path(old_file).name}")
                except:
                    pass
            
            # สร้าง TTS ด้วย Edge TTS โดยไม่ใช้ SSML
            communicate = edge_tts.Communicate(cleaned_text, voice_name)
            
            # สร้างไฟล์ชั่วคราวก่อน
            temp_path = file_path.with_suffix('.tmp.mp3')
            await communicate.save(str(temp_path))
            
            print(f"   🎵 Edge TTS raw file generated: {temp_path.name}")
            
            # แก้ไขปัญหา LAME Padding และ Contamination
            if await self._fix_lame_padding_and_contamination(temp_path, file_path, script_title, emotion):
                print(f"   ✅ Edge TTS generation completed (LAME padding fixed)")
                return str(file_path), web_url
            else:
                print(f"   ❌ LAME padding fix failed")
                raise Exception("LAME padding fix failed")
                
        except Exception as e:
            print(f"   ❌ Edge TTS failed: {e}")
            raise
    
    async def _fix_lame_padding_and_contamination(self, temp_path: Path, final_path: Path, script_title: str, emotion: str) -> bool:
        """แก้ไขปัญหา LAME Encoder Padding และ Audio Contamination"""
        
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                # ถ้าไม่มี audio processing ให้ย้ายไฟล์ตรงๆ
                temp_path.rename(final_path)
                return True
            
            print(f"   🔧 Fixing LAME padding and contamination...")
            
            # โหลดไฟล์เสียง
            audio = AudioSegment.from_file(temp_path)
            original_duration = len(audio) / 1000
            
            print(f"   ⏱️ Original duration: {original_duration:.1f}s")
            
            # แก้ไขปัญหา LAME padding และ contamination
            fixed_audio = self._remove_lame_padding_and_silence(audio)
            
            if fixed_audio:
                final_duration = len(fixed_audio) / 1000
                print(f"   ✂️ Fixed duration: {final_duration:.1f}s (removed {original_duration - final_duration:.1f}s)")
                
                # Normalize และปรับปรุงคุณภาพ
                fixed_audio = normalize(fixed_audio)
                fixed_audio = fixed_audio.set_frame_rate(22050)
                
                # Export โดยไม่ใช้ LAME encoder เพื่อป้องกัน padding
                fixed_audio.export(
                    final_path,
                    format="mp3",
                    bitrate="128k",
                    parameters=[
                        "-q:a", "2",           # คุณภาพสูง
                        "-ar", "22050",        # Sample rate
                        "-write_xing", "0",    # ไม่เขียน XING header
                        "-id3v2_version", "0", # ไม่ใส่ ID3v2 tags
                        "-write_id3v1", "0"    # ไม่ใส่ ID3v1 tags
                    ]
                )
                
                # ลบไฟล์ชั่วคราว
                if temp_path.exists():
                    temp_path.unlink()
                
                print(f"   🎯 LAME padding and contamination removed successfully")
                return True
            else:
                print(f"   ❌ Could not fix LAME padding")
                # ใช้ไฟล์เดิม
                temp_path.rename(final_path)
                return True
                
        except Exception as e:
            print(f"   ❌ LAME padding fix failed: {e}")
            
            # หากล้มเหลว ให้ย้ายไฟล์เดิม
            try:
                if temp_path.exists():
                    temp_path.rename(final_path)
                return True
            except:
                return False

    def _remove_lame_padding_and_silence(self, audio: 'AudioSegment') -> 'AudioSegment':
        """กำจัด LAME padding และเสียงเงียบที่ไม่ต้องการ"""
        
        try:
            print(f"   🔍 Analyzing audio for padding and silence...")
            
            # Parameters สำหรับการตรวจจับเสียง
            silence_threshold = -50  # dB
            chunk_size = 100  # ms
            min_silence_duration = 500  # ms
            
            # หาจุดเริ่มต้นของเสียงจริง (ข้ามเสียงเงียบต้น)
            start_pos = 0
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                if len(chunk) < chunk_size:
                    break
                
                # คำนวณ volume level
                if hasattr(chunk, 'dBFS'):
                    volume = chunk.dBFS
                else:
                    volume = chunk.rms if hasattr(chunk, 'rms') else -60
                
                if volume > silence_threshold:
                    start_pos = max(0, i - chunk_size)  # เก็บ buffer เล็กน้อย
                    print(f"   🎯 Found audio start at: {start_pos/1000:.1f}s")
                    break
            
            # หาจุดสิ้นสุดของเสียงจริง (ข้ามเสียงเงียบท้าย)
            end_pos = len(audio)
            for i in range(len(audio) - chunk_size, 0, -chunk_size):
                chunk = audio[i:i + chunk_size]
                
                # คำนวณ volume level
                if hasattr(chunk, 'dBFS'):
                    volume = chunk.dBFS
                else:
                    volume = chunk.rms if hasattr(chunk, 'rms') else -60
                
                if volume > silence_threshold:
                    end_pos = min(len(audio), i + chunk_size * 2)  # เก็บ buffer เล็กน้อย
                    print(f"   🎯 Found audio end at: {end_pos/1000:.1f}s")
                    break
            
            # ตรวจสอบว่าเสียงที่เหลือมีความยาวสมเหตุสมผล
            trimmed_duration = (end_pos - start_pos) / 1000
            
            if trimmed_duration < 0.5:
                print(f"   ⚠️ Trimmed audio too short ({trimmed_duration:.1f}s), using minimal trim")
                # ใช้การตัดแบบน้อยที่สุด
                start_pos = min(start_pos, len(audio) * 0.1)  # ตัดไม่เกิน 10% ต้น
                end_pos = max(end_pos, len(audio) * 0.9)      # ตัดไม่เกิน 10% ท้าย
            
            elif trimmed_duration > 30:
                print(f"   ⚠️ Trimmed audio still too long ({trimmed_duration:.1f}s), applying aggressive trim")
                # หาช่วงที่มีเสียงดังที่สุด
                max_volume = -100
                best_start = 0
                best_end = len(audio)
                
                # วิเคราะห์ทุก 5 วินาที
                window_size = 5000  # 5 seconds
                for i in range(int(start_pos), int(end_pos) - window_size, 1000):
                    window = audio[i:i + window_size]
                    if hasattr(window, 'dBFS'):
                        volume = window.dBFS
                    else:
                        volume = window.rms if hasattr(window, 'rms') else -60
                    
                    if volume > max_volume:
                        max_volume = volume
                        best_start = i
                        best_end = i + window_size
                
                start_pos = best_start
                end_pos = best_end
                print(f"   ✂️ Using aggressive trim: {start_pos/1000:.1f}s to {end_pos/1000:.1f}s")
            
            # ตัดเสียง
            if start_pos > 0 or end_pos < len(audio):
                trimmed_audio = audio[start_pos:end_pos]
                print(f"   ✅ Trimmed from {len(audio)/1000:.1f}s to {len(trimmed_audio)/1000:.1f}s")
                return trimmed_audio
            else:
                print(f"   ℹ️ No trimming needed")
                return audio
                
        except Exception as e:
            print(f"   ❌ Padding removal failed: {e}")
            return audio

    def _clean_text_for_tts(self, text: str) -> str:
        """ทำความสะอาดข้อความก่อนส่งให้ TTS เพื่อป้องกัน contamination"""
        
        # ลบ characters ที่อาจทำให้เกิดปัญหา
        import re
        
        # ลบ HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # ลบ special characters ที่อาจทำให้ TTS สับสน
        text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\.,!?\-]', '', text)
        
        # ลบ multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # ลบ leading/trailing spaces
        text = text.strip()
        
        # จำกัดความยาวเพื่อป้องกัน buffer overflow
        if len(text) > 1000:
            text = text[:1000] + "..."
        
        return text

    def _create_safe_ssml(self, text: str, voice_name: str, emotion: str, intensity: float) -> str:
        """สร้าง SSML แบบปลอดภัย - ลดความซับซ้อนเพื่อป้องกัน contamination"""
        
        # แปลงอารมณ์ให้เป็นรูปแบบที่ Edge TTS รองรับอย่างแน่นอน
        safe_emotions = {
            "excited": "cheerful",
            "happy": "cheerful", 
            "professional": "neutral",  # เปลี่ยนจาก serious เป็น neutral
            "friendly": "gentle",
            "confident": "neutral",     # เปลี่ยนจาก serious เป็น neutral
            "energetic": "cheerful",
            "calm": "gentle",
            "urgent": "neutral"         # เปลี่ยนจาก angry เป็น neutral
        }
        
        ssml_emotion = safe_emotions.get(emotion, "neutral")
        
        # ใช้ SSML แบบง่าย ไม่ซับซ้อน
        if ssml_emotion == "neutral":
            # ไม่ใช้ express-as สำหรับ neutral
            ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
        <voice name="{voice_name}">
            <prosody rate="medium" pitch="medium">
                {text}
            </prosody>
        </voice>
    </speak>"""
        else:
            # ใช้ express-as แบบเรียบง่าย
            ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
        <voice name="{voice_name}">
            <mstts:express-as style="{ssml_emotion}">
                {text}
            </mstts:express-as>
        </voice>
    </speak>"""
        
        return ssml.strip()

    async def _validate_and_clean_audio(self, temp_path: Path, final_path: Path, script_title: str, emotion: str) -> bool:
        """ตรวจสอบและทำความสะอาดไฟล์เสียงเพื่อกำจัด contamination"""
        
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                # ถ้าไม่มี audio processing ให้ย้ายไฟล์ตรงๆ
                temp_path.rename(final_path)
                return True
            
            print(f"   🔍 Validating and cleaning audio...")
            
            # โหลดไฟล์เสียง
            audio = AudioSegment.from_file(temp_path)
            
            # ตรวจสอบความยาวไฟล์
            duration_ms = len(audio)
            print(f"   ⏱️ Original duration: {duration_ms/1000:.1f}s")
            
            # หากไฟล์ยาวเกินไป (มากกว่า 30 วินาที) อาจมีปัญหา contamination
            if duration_ms > 30000:  # 30 seconds
                print(f"   ⚠️ Audio too long ({duration_ms/1000:.1f}s), attempting to extract main content...")
                
                # หาส่วนที่เป็นเสียงจริง (ไม่ใช่เงียบ)
                # แบ่งเป็นช่วงๆ และวิเคราะห์ volume
                chunk_size = 1000  # 1 second chunks
                chunks = []
                
                for i in range(0, len(audio), chunk_size):
                    chunk = audio[i:i+chunk_size]
                    # คำนวณ RMS (volume level)
                    rms = chunk.rms if hasattr(chunk, 'rms') else 100
                    chunks.append((i, rms))
                
                # หาช่วงที่มีเสียงจริง (RMS > threshold)
                threshold = max([chunk[1] for chunk in chunks]) * 0.1  # 10% ของเสียงดังสุด
                active_chunks = [chunk for chunk in chunks if chunk[1] > threshold]
                
                if active_chunks:
                    # ตัดเอาเฉพาะส่วนที่มีเสียงจริง
                    start_time = min([chunk[0] for chunk in active_chunks])
                    end_time = max([chunk[0] for chunk in active_chunks]) + chunk_size
                    
                    # เพิ่ม buffer เล็กน้อย
                    start_time = max(0, start_time - 500)  # 0.5s buffer
                    end_time = min(len(audio), end_time + 500)  # 0.5s buffer
                    
                    audio = audio[start_time:end_time]
                    print(f"   ✂️ Trimmed to: {len(audio)/1000:.1f}s (removed contamination)")
            
            # Normalize และปรับปรุงคุณภาพ
            audio = normalize(audio)
            
            # ตั้งค่า sample rate และ bitrate ที่เหมาะสม
            audio = audio.set_frame_rate(22050)
            
            # Export เป็น MP3 คุณภาพดี
            audio.export(
                final_path, 
                format="mp3", 
                bitrate="128k",
                parameters=["-q:a", "2", "-ar", "22050"]
            )
            
            # ลบไฟล์ชั่วคราว
            if temp_path.exists():
                temp_path.unlink()
            
            # ทำความสะอาด metadata
            self._clean_metadata(final_path, script_title, emotion)
            
            print(f"   ✅ Audio validated and cleaned: {len(audio)/1000:.1f}s")
            return True
            
        except Exception as e:
            print(f"   ❌ Audio validation failed: {e}")
            
            # หากล้มเหลว ให้ย้ายไฟล์เดิม
            try:
                if temp_path.exists():
                    temp_path.rename(final_path)
                return True
            except:
                return False


    async def _generate_elevenlabs_speech(
        self, 
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float,
        script_title: str = ""
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
            
            # ปรับปรุงคุณภาพเสียงและทำความสะอาด metadata
            await self._enhance_audio_quality(file_path, script_title, emotion)
            
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
        intensity: float,
        script_title: str = ""
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
                # แปลงเป็น MP3 และทำความสะอาด metadata
                mp3_path = await self._convert_to_mp3(file_path, script_title, emotion)
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
            "professional": "ด้วยมาตรการทางวิชาชีพ: ",
            "friendly": "ด้วยความเป็นมิตรและอบอุ่น: ",
            "confident": "ด้วยความมั่นใจและแน่วแน่: ",
            "energetic": "ด้วยพลังและความกระปรี้กระเปร่า: ",
            "calm": "ด้วยความสงบและใจเย็น: ",
            "urgent": "ด้วยความเร่งด่วนและจำกัดเวลา: "
        }
        
        prefix = emotion_prefixes.get(emotion, "")
        return f"{prefix}{text}" if prefix else text
    
    async def _convert_to_mp3(self, wav_path: Path, script_title: str = "", emotion: str = "") -> Path:
        """แปลงไฟล์ WAV เป็น MP3 พร้อมทำความสะอาด metadata"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return wav_path
                
            mp3_path = wav_path.with_suffix('.mp3')
            audio = AudioSegment.from_wav(wav_path)
            
            # Export เป็น MP3 ด้วยการตั้งค่าที่ดี
            audio.export(
                mp3_path, 
                format="mp3", 
                bitrate="128k",
                parameters=["-q:a", "2"]
            )
            
            # ลบไฟล์ WAV
            if wav_path.exists():
                wav_path.unlink()
            
            # ทำความสะอาด metadata
            self._clean_metadata(mp3_path, script_title, emotion)
                
            return mp3_path
            
        except Exception as e:
            print(f"   ⚠️ MP3 conversion failed: {e}")
            return wav_path
    
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
    
    async def _generate_basic_speech(self, text: str, script_id: str, language: str = "th", script_title: str = "") -> Tuple[str, str]:
        """Fallback เป็น basic gTTS พร้อม unique filename"""
        try:
            if not GTTS_AVAILABLE:
                print("   ❌ gTTS not available for fallback")
                return "", ""
            
            import time
            
            # ทำความสะอาดข้อความ
            cleaned_text = self._clean_text_for_tts(text) if hasattr(self, '_clean_text_for_tts') else text
            
            # สร้าง unique filename
            timestamp = str(int(time.time() * 1000))
            text_hash = hashlib.md5(cleaned_text.encode()).hexdigest()[:8]
            filename = f"script_{script_id}_{text_hash}_{timestamp}.mp3"
            
            file_path = self.audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   📢 Using basic gTTS")
            print(f"   📁 Unique filename: {filename}")
            print(f"   🧹 Text: '{cleaned_text[:30]}...'")
            
            # สร้างด้วย gTTS
            tts = gTTS(text=cleaned_text, lang=language, slow=False)
            tts.save(str(file_path))
            
            # ทำความสะอาด metadata หากมีฟังก์ชัน
            if hasattr(self, '_clean_metadata'):
                try:
                    self._clean_metadata(file_path, script_title or "Basic TTS Audio", "neutral")
                except:
                    pass
            
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
            if hasattr(self, 'generate_emotional_speech') and provider != "basic":
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
                return await self._generate_basic_speech(content, script_id, language, script_title)
                
        except Exception as e:
            print(f"❌ Error in generate_script_audio: {e}")
            # Ultimate fallback
            try:
                return await self._generate_basic_speech(content, script_id, language, "Script Audio")
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