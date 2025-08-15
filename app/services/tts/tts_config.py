# app/services/tts/tts_config.py
"""TTS Service Configuration and Dependencies Management"""

import os
from typing import Dict, Any

# Safe TTS Providers Import
EDGE_TTS_AVAILABLE = False
ELEVENLABS_AVAILABLE = False
AZURE_AVAILABLE = False
AUDIO_PROCESSING_AVAILABLE = False
GTTS_AVAILABLE = False

def load_dependencies():
    """Load all TTS dependencies safely"""
    global EDGE_TTS_AVAILABLE, ELEVENLABS_AVAILABLE, AZURE_AVAILABLE
    global AUDIO_PROCESSING_AVAILABLE, GTTS_AVAILABLE
    
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
        from mutagen.mp3 import MP3
        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON
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

class TTSConfig:
    """TTS Configuration Manager"""
    
    def __init__(self):
        self.elevenlabs_api_key = None
        self.azure_speech_key = None
        self.azure_speech_region = "southeastasia"
        self._load_api_keys()
    
    def _load_api_keys(self):
        """โหลด API keys จาก environment variables"""
        try:
            self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY") 
            self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION", "southeastasia")
            
            # Configure ElevenLabs if available
            if self.elevenlabs_api_key and ELEVENLABS_AVAILABLE:
                try:
                    from elevenlabs import set_api_key
                    set_api_key(self.elevenlabs_api_key)
                    print("✅ ElevenLabs API key configured")
                except Exception as e:
                    print(f"⚠️ ElevenLabs configuration failed: {e}")
            else:
                if not self.elevenlabs_api_key:
                    print("ℹ️ ElevenLabs API key not found (optional)")
            
            # Azure configuration
            if self.azure_speech_key and AZURE_AVAILABLE:
                print("✅ Azure Speech API key configured")
            else:
                if not self.azure_speech_key:
                    print("ℹ️ Azure Speech API key not found (optional)")
                
        except Exception as e:
            print(f"⚠️ Error loading API keys: {e}")
            self.elevenlabs_api_key = None
            self.azure_speech_key = None

    def get_provider_config(self) -> Dict[str, Any]:
        """รายการ provider configurations"""
        return {
            "edge": {
                "available": EDGE_TTS_AVAILABLE,
                "voices": {},
                "supports_emotions": True,
                "quality": "high",
                "cost": "free"
            },
            "elevenlabs": {
                "available": ELEVENLABS_AVAILABLE and bool(self.elevenlabs_api_key),
                "voices": {},
                "supports_emotions": True,
                "quality": "premium",
                "cost": "paid"
            },
            "azure": {
                "available": AZURE_AVAILABLE and bool(self.azure_speech_key),
                "voices": {},
                "supports_emotions": True,
                "quality": "enterprise",
                "cost": "paid"
            }
        }

# Initialize dependencies on import
load_dependencies()