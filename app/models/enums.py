# app/models/enums.py
"""
Enum definitions for AI Live Commerce Platform
Contains all enum types used across the script-related models
"""

import enum

class ScriptType(enum.Enum):
    """Type of script generation"""
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"

class ScriptStatus(enum.Enum):
    """Status of script in workflow"""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"

class MP3Status(enum.Enum):
    """Status of MP3 file generation"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoType(enum.Enum):
    """Type of video content"""
    BACKGROUND = "background"
    PRODUCT_DEMO = "product_demo"
    LIFESTYLE = "lifestyle"

class GenderType(enum.Enum):
    """Gender classification for voice personas"""
    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"