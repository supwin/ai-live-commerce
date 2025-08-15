# app/models/__init__.py
"""
Model imports for AI Live Commerce Platform
Import all models to make them available throughout the application
"""

# Import enums first (no dependencies)
from .enums import (
    ScriptType,
    ScriptStatus, 
    MP3Status,
    VideoType,
    GenderType
)

# Import base model
from .base import Base

# Import individual models
from .script import Script
from .mp3 import MP3File
from .video import Video
from .script_persona import ScriptPersona
from .voice_persona import VoicePersona

# Make all models available when importing from models package
__all__ = [
    # Enums
    "ScriptType",
    "ScriptStatus",
    "MP3Status", 
    "VideoType",
    "GenderType",
    
    # Base
    "Base",
    
    # Models
    "Script",
    "MP3File", 
    "Video",
    "ScriptPersona",
    "VoicePersona"
]