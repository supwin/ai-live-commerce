# app/services/tts/audio_processor.py
"""Audio Processing and Metadata Management"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional

from .tts_config import AUDIO_PROCESSING_AVAILABLE

if AUDIO_PROCESSING_AVAILABLE:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON

class AudioProcessor:
    """Audio Processing and Enhancement Manager"""
    
    @staticmethod
    def clean_text_for_tts(text: str) -> str:
        """ทำความสะอาดข้อความก่อนส่งให้ TTS เพื่อป้องกัน contamination"""
        
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

    @staticmethod
    def clean_metadata(file_path: Path, script_title: str = "", emotion: str = ""):
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
            audio_file.tags.add(TIT2(encoding=3, text=script_title or "AI Live Commerce Script"))
            audio_file.tags.add(TPE1(encoding=3, text="AI Live Commerce TTS"))
            audio_file.tags.add(TALB(encoding=3, text="Product Scripts"))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            audio_file.tags.add(TCON(encoding=3, text=f"Speech/{emotion}"))
            
            # บันทึก metadata ใหม่
            audio_file.save()
            
            print("   🏷️ Metadata cleaned and updated")
            
        except Exception as e:
            print(f"   ⚠️ Metadata cleaning failed: {e}")
            # ไม่ throw error เพราะไฟล์ยังใช้งานได้

    @staticmethod
    async def enhance_audio_quality(file_path: Path, script_title: str = "", emotion: str = ""):
        """ปรับปรุงคุณภาพเสียงและทำความสะอาด metadata"""
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                return
                
            print("   🎧 Enhancing audio quality...")
            
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
            AudioProcessor.clean_metadata(file_path, script_title, emotion)
            
            print("   ✅ Audio quality enhanced and metadata cleaned")
            
        except Exception as e:
            print(f"   ⚠️ Audio enhancement failed: {e}")
            # ลองทำความสะอาด metadata อย่างเดียว
            try:
                AudioProcessor.clean_metadata(file_path, script_title, emotion)
            except:
                pass

    @staticmethod
    async def fix_lame_padding_and_contamination(temp_path: Path, final_path: Path, script_title: str, emotion: str) -> bool:
        """แก้ไขปัญหา LAME Encoder Padding และ Audio Contamination"""
        
        try:
            if not AUDIO_PROCESSING_AVAILABLE:
                # ถ้าไม่มี audio processing ให้ย้ายไฟล์ตรงๆ
                temp_path.rename(final_path)
                return True
            
            print("   🔧 Fixing LAME padding and contamination...")
            
            # โหลดไฟล์เสียง
            audio = AudioSegment.from_file(temp_path)
            original_duration = len(audio) / 1000
            
            print(f"   ⏱️ Original duration: {original_duration:.1f}s")
            
            # แก้ไขปัญหา LAME padding และ contamination
            fixed_audio = AudioProcessor._remove_lame_padding_and_silence(audio)
            
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
                
                print("   🎯 LAME padding and contamination removed successfully")
                return True
            else:
                print("   ❌ Could not fix LAME padding")
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

    @staticmethod
    def _remove_lame_padding_and_silence(audio: 'AudioSegment') -> 'AudioSegment':
        """กำจัด LAME padding และเสียงเงียบที่ไม่ต้องการ"""
        
        try:
            print("   🔍 Analyzing audio for padding and silence...")
            
            # Parameters สำหรับการตรวจจับเสียง
            silence_threshold = -50  # dB
            chunk_size = 100  # ms
            
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
            
            # ตัดเสียง
            if start_pos > 0 or end_pos < len(audio):
                trimmed_audio = audio[start_pos:end_pos]
                print(f"   ✅ Trimmed from {len(audio)/1000:.1f}s to {len(trimmed_audio)/1000:.1f}s")
                return trimmed_audio
            else:
                print("   ℹ️ No trimming needed")
                return audio
                
        except Exception as e:
            print(f"   ❌ Padding removal failed: {e}")
            return audio

    @staticmethod
    async def convert_to_mp3(wav_path: Path, script_title: str = "", emotion: str = "") -> Path:
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
            AudioProcessor.clean_metadata(mp3_path, script_title, emotion)
                
            return mp3_path
            
        except Exception as e:
            print(f"   ⚠️ MP3 conversion failed: {e}")
            return wav_path