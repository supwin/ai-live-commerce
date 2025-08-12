# app/services/tts_service.py
"""
Text-to-Speech service using Google TTS
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
from gtts import gTTS
import hashlib
import tempfile
import aiofiles

class TTSService:
    """Text-to-Speech service"""
    
    def __init__(self):
        self.audio_dir = Path("frontend/static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Supported languages
        self.languages = {
            'th': 'Thai',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese'
        }
        
    def _get_audio_path(self, script_id: str) -> Path:
        """Get audio file path for script"""
        return self.audio_dir / f"{script_id}.mp3"
    
    def _get_audio_url(self, script_id: str) -> str:
        """Get audio file URL for web access"""
        return f"/static/audio/{script_id}.mp3"
    
    async def generate_speech(
        self, 
        text: str, 
        script_id: str, 
        language: str = 'th',
        slow: bool = False
    ) -> tuple[str, str]:
        """
        Generate speech audio from text
        
        Args:
            text: Text to convert to speech
            script_id: Script ID for filename
            language: Language code (th, en, ja, ko, zh)
            slow: Slow speech speed
            
        Returns:
            tuple: (file_path, web_url)
        """
        
        if language not in self.languages:
            language = 'th'  # Default to Thai
            
        audio_path = self._get_audio_path(script_id)
        audio_url = self._get_audio_url(script_id)
        
        # Check if file already exists
        if audio_path.exists():
            return str(audio_path), audio_url
        
        try:
            # Create TTS object
            tts = gTTS(
                text=text,
                lang=language,
                slow=slow
            )
            
            # Save to temporary file first
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_path = temp_file.name
                
            # Generate audio file
            await asyncio.to_thread(tts.save, temp_path)
            
            # Move to final location
            os.rename(temp_path, audio_path)
            
            print(f"✅ Generated TTS audio: {audio_path}")
            return str(audio_path), audio_url
            
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            # Return empty if failed
            return "", ""
    
    async def generate_script_audio(
        self,
        script_id: str,
        content: str,
        language: str = 'th'
    ) -> tuple[str, str]:
        """Generate audio for a script"""
        return await self.generate_speech(
            text=content,
            script_id=script_id,
            language=language
        )
    
    def get_script_audio_url(self, script_id: str) -> Optional[str]:
        """Get audio URL if file exists"""
        audio_path = self._get_audio_path(script_id)
        if audio_path.exists():
            return self._get_audio_url(script_id)
        return None
    
    def delete_script_audio(self, script_id: str) -> bool:
        """Delete audio file for script"""
        audio_path = self._get_audio_path(script_id)
        try:
            if audio_path.exists():
                audio_path.unlink()
                print(f"🗑️ Deleted audio: {audio_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to delete audio: {e}")
            return False
    
    async def cleanup_unused_audio(self, existing_script_ids: list[str]):
        """Clean up audio files for deleted scripts"""
        if not self.audio_dir.exists():
            return
            
        deleted_count = 0
        
        for audio_file in self.audio_dir.glob("*.mp3"):
            script_id = audio_file.stem
            if script_id not in existing_script_ids:
                try:
                    audio_file.unlink()
                    deleted_count += 1
                    print(f"🧹 Cleaned up unused audio: {audio_file}")
                except Exception as e:
                    print(f"❌ Failed to cleanup {audio_file}: {e}")
        
        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} unused audio files")
    
    def get_audio_stats(self) -> dict:
        """Get audio files statistics"""
        if not self.audio_dir.exists():
            return {"count": 0, "total_size": 0}
            
        audio_files = list(self.audio_dir.glob("*.mp3"))
        total_size = sum(f.stat().st_size for f in audio_files)
        
        return {
            "count": len(audio_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

# Global TTS service instance
tts_service = TTSService()