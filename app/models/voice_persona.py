# app/models/voice_persona.py
"""
Voice persona model for AI Live Commerce Platform
Handles TTS voice configurations and characteristics
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import GenderType

class VoicePersona(Base):
    """
    Voice persona model for TTS generation
    
    Responsibilities:
    - Store TTS provider configurations
    - Manage voice characteristics and parameters
    - Handle emotional capabilities and ranges
    - Track usage statistics and quality ratings
    - Provide TTS configuration for audio generation
    """
    __tablename__ = "voice_personas"
    
    # Basic Information
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # TTS Configuration
    tts_provider = Column(String(50), nullable=False)  # edge, google, elevenlabs
    voice_id = Column(String(100), nullable=False)  # Provider-specific voice ID
    language = Column(String(10), default="th")  # th, en, etc.
    
    # Voice Characteristics
    gender = Column(Enum(GenderType), default=GenderType.FEMALE)
    age_range = Column(String(20))  # young, adult, senior
    accent = Column(String(50))  # thai_central, thai_northern, american, british
    
    # Voice Parameters
    speed = Column(DECIMAL(3,2), default=1.0)  # 0.5 - 2.0
    pitch = Column(DECIMAL(3,2), default=1.0)  # 0.5 - 2.0
    volume = Column(DECIMAL(3,2), default=1.0)  # 0.5 - 2.0
    
    # Emotional Capabilities
    emotion = Column(String(50))  # calm, excited, professional
    emotional_range = Column(JSON)  # Emotions this voice can express
    
    # Provider-Specific Settings
    provider_settings = Column(JSON)  # Additional provider-specific parameters
    
    # Quality and Usage
    sample_audio_path = Column(String(500))  # Path to sample audio
    quality_rating = Column(Integer, default=0)  # 1-5 stars
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)  # Premium voices (paid)
    
    # Usage Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5,2), default=0.0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    mp3_files = relationship("MP3File", back_populates="voice_persona")
    
    def __repr__(self):
        return f"<VoicePersona {self.id}: {self.name}>"
    
    @property
    def emotions_list(self):
        """Get emotional range as list"""
        return self.emotional_range or ["neutral"]
    
    @property
    def full_name(self):
        """Get full descriptive name"""
        parts = [self.name]
        if self.gender:
            parts.append(f"({self.gender.value})")
        if self.age_range:
            parts.append(f"- {self.age_range}")
        return " ".join(parts)
    
    def get_tts_config(self):
        """Get TTS configuration for generation"""
        config = {
            "provider": self.tts_provider,
            "voice_id": self.voice_id,
            "language": self.language,
            "speed": float(self.speed),
            "pitch": float(self.pitch),
            "volume": float(self.volume)
        }
        
        # Add provider-specific settings
        if self.provider_settings:
            config.update(self.provider_settings)
            
        return config
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "tts_provider": self.tts_provider,
            "voice_id": self.voice_id,
            "language": self.language,
            "gender": self.gender.value if self.gender else None,
            "age_range": self.age_range,
            "accent": self.accent,
            "speed": float(self.speed),
            "pitch": float(self.pitch),
            "volume": float(self.volume),
            "emotion": self.emotion,
            "emotional_range": self.emotional_range or [],
            "provider_settings": self.provider_settings or {},
            "sample_audio_path": self.sample_audio_path,
            "quality_rating": self.quality_rating,
            "is_active": self.is_active,
            "is_premium": self.is_premium,
            "usage_count": self.usage_count,
            "success_rate": float(self.success_rate) if self.success_rate else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }