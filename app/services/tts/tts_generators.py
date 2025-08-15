# app/services/tts/tts_generators.py
"""TTS Generator Classes for Different Providers"""

import hashlib
import time
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional

from .tts_config import (
    EDGE_TTS_AVAILABLE, ELEVENLABS_AVAILABLE, AZURE_AVAILABLE, GTTS_AVAILABLE,
    TTSConfig
)
from .voice_providers import VoiceProviders
from .audio_processor import AudioProcessor

if EDGE_TTS_AVAILABLE:
    import edge_tts

if ELEVENLABS_AVAILABLE:
    from elevenlabs import generate

if AZURE_AVAILABLE:
    import azure.cognitiveservices.speech as speechsdk

if GTTS_AVAILABLE:
    from gtts import gTTS

class EdgeTTSGenerator:
    """Edge TTS Generator"""
    
    @staticmethod
    async def generate(
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float,
        script_title: str,
        audio_dir: Path
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย Edge TTS แก้ไขปัญหา LAME Padding และ Filename Collision"""
        
        try:
            # เลือกเสียงจาก voice_config หรือใช้ default
            voice_name = voice_config.get("voice", "th-TH-PremwadeeNeural")
            
            # ทำความสะอาดข้อความก่อนประมวลผล
            cleaned_text = AudioProcessor.clean_text_for_tts(text)
            
            # สร้าง unique filename ที่รวม timestamp และ text hash
            timestamp = str(int(time.time() * 1000))  # milliseconds
            text_hash = hashlib.md5(cleaned_text.encode()).hexdigest()[:8]
            filename = f"script_{script_id}_{text_hash}_{timestamp}.mp3"
            
            file_path = audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   📝 Using plain text (no SSML) to prevent concatenation")
            print(f"   🧹 Text: '{cleaned_text}'")
            print(f"   📁 Unique filename: {filename}")
            
            # ลบไฟล์เก่าหากมี (ใช้ pattern เดิม)
            old_pattern = f"script_{script_id}_{text_hash}_*.mp3"
            import glob
            for old_file in glob.glob(str(audio_dir / old_pattern)):
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
            if await AudioProcessor.fix_lame_padding_and_contamination(temp_path, file_path, script_title, emotion):
                print(f"   ✅ Edge TTS generation completed (LAME padding fixed)")
                return str(file_path), web_url
            else:
                print(f"   ❌ LAME padding fix failed")
                raise Exception("LAME padding fix failed")
                
        except Exception as e:
            print(f"   ❌ Edge TTS failed: {e}")
            raise

class ElevenLabsGenerator:
    """ElevenLabs TTS Generator"""
    
    @staticmethod
    async def generate(
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float,
        script_title: str,
        audio_dir: Path
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย ElevenLabs AI"""
        
        try:
            voice_id = voice_config.get("voice_id", "pNInz6obpgDQGcFmaJgB")
            
            # ปรับ text สำหรับอารมณ์
            emotional_prefixes = VoiceProviders.get_emotional_prefixes()
            prefix = emotional_prefixes.get(emotion, "")
            emotional_text = f"{prefix}{text}" if prefix else text
            
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.mp3"
            file_path = audio_dir / filename
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
            await AudioProcessor.enhance_audio_quality(file_path, script_title, emotion)
            
            print(f"   ✅ ElevenLabs generation completed")
            return str(file_path), web_url
            
        except Exception as e:
            print(f"   ❌ ElevenLabs failed: {e}")
            raise

class AzureGenerator:
    """Azure Cognitive Services TTS Generator"""
    
    @staticmethod
    async def generate(
        text: str, 
        script_id: str, 
        voice_config: Dict, 
        emotion: str, 
        intensity: float,
        script_title: str,
        audio_dir: Path,
        config: TTSConfig
    ) -> Tuple[str, str]:
        """สร้างเสียงด้วย Azure Cognitive Services"""
        
        try:
            # สร้าง Azure Speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=config.azure_speech_key, 
                region=config.azure_speech_region
            )
            
            voice_name = voice_config.get("voice", "th-TH-PremwadeeNeural")
            speech_config.speech_synthesis_voice_name = voice_name
            
            filename = f"script_{script_id}_{hashlib.md5(text.encode()).hexdigest()[:8]}.wav"
            file_path = audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            # สร้าง SSML พร้อมอารมณ์
            ssml_text = AzureGenerator._create_emotional_ssml(text, voice_name, emotion, intensity)
            
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
                mp3_path = await AudioProcessor.convert_to_mp3(file_path, script_title, emotion)
                print(f"   ✅ Azure Speech generation completed")
                return str(mp3_path), web_url.replace('.wav', '.mp3')
            else:
                raise Exception(f"Azure synthesis failed: {result.reason}")
                
        except Exception as e:
            print(f"   ❌ Azure Speech failed: {e}")
            raise
    
    @staticmethod
    def _create_emotional_ssml(text: str, voice_name: str, emotion: str, intensity: float) -> str:
        """สร้าง SSML ที่รองรับอารมณ์"""
        
        # แปลงอารมณ์ให้เหมาะสมกับ SSML
        emotion_mapping = VoiceProviders.get_emotion_mapping()
        ssml_emotion = emotion_mapping.get(emotion, emotion)
        
        # ปรับ intensity
        intensity_level = "strong" if intensity > 1.5 else "moderate" if intensity > 1.0 else "mild"
        
        # ดึงการตั้งค่า prosody
        prosody_settings = VoiceProviders.get_prosody_settings(emotion)
        
        # สร้าง SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="th-TH">
            <voice name="{voice_name}">
                <mstts:express-as style="{ssml_emotion}" styledegree="{intensity}">
                    <prosody rate="{prosody_settings['rate']}" pitch="{prosody_settings['pitch']}">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        return ssml.strip()

class BasicTTSGenerator:
    """Basic gTTS Fallback Generator"""
    
    @staticmethod
    async def generate(
        text: str, 
        script_id: str, 
        language: str,
        script_title: str,
        audio_dir: Path
    ) -> Tuple[str, str]:
        """Fallback เป็น basic gTTS พร้อม unique filename"""
        try:
            if not GTTS_AVAILABLE:
                print("   ❌ gTTS not available for fallback")
                return "", ""
            
            # ทำความสะอาดข้อความ
            cleaned_text = AudioProcessor.clean_text_for_tts(text)
            
            # สร้าง unique filename
            timestamp = str(int(time.time() * 1000))
            text_hash = hashlib.md5(cleaned_text.encode()).hexdigest()[:8]
            filename = f"script_{script_id}_{text_hash}_{timestamp}.mp3"
            
            file_path = audio_dir / filename
            web_url = f"/static/audio/{filename}"
            
            print(f"   📢 Using basic gTTS")
            print(f"   📁 Unique filename: {filename}")
            print(f"   🧹 Text: '{cleaned_text[:30]}...'")
            
            # สร้างด้วย gTTS
            tts = gTTS(text=cleaned_text, lang=language, slow=False)
            tts.save(str(file_path))
            
            # ทำความสะอาด metadata หากมีฟังก์ชัน
            try:
                AudioProcessor.clean_metadata(file_path, script_title or "Basic TTS Audio", "neutral")
            except:
                pass
            
            print(f"   ✅ Basic gTTS generation completed")
            return str(file_path), web_url
            
        except Exception as e:
            print(f"   ❌ Basic TTS failed: {e}")
            return "", ""