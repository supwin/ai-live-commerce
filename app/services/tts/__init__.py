# app/services/tts/__init__.py
"""
TTS Package Initialization
นำเข้าและเปิดใช้งาน Enhanced TTS Service
"""

from .enhanced_tts_service import enhanced_tts_service, EnhancedTTSService

# เพื่อให้สามารถ import ได้โดยตรง
__all__ = ['enhanced_tts_service', 'EnhancedTTSService']