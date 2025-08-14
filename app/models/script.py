# app/models/script.py
"""
Script-related models for AI Live Commerce Platform
Handles scripts, MP3 files, personas, and related data
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class ScriptType(enum.Enum):
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"

class ScriptStatus(enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    ARCHIVED = "ARCHIVED"

class MP3Status(enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoType(enum.Enum):
    BACKGROUND = "background"
    PRODUCT_DEMO = "product_demo"
    LIFESTYLE = "lifestyle"

class GenderType(enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    NEUTRAL = "NEUTRAL"

class Script(Base):
    """Script model for product scripts"""
    __tablename__ = "scripts"
    
    # Basic Information
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    
    # Script Details
    script_type = Column(Enum(ScriptType), default=ScriptType.AI_GENERATED)
    persona_id = Column(Integer, ForeignKey("script_personas.id"), nullable=True)
    language = Column(String(10), default="th")
    
    # AI Generation Details
    target_emotion = Column(String(50))  # excited, professional, friendly, etc.
    tone = Column(String(50))  # energetic, calm, professional
    call_to_action = Column(String(255))
    
    # Estimated duration in seconds
    duration_estimate = Column(Integer)
    
    # Status and Permissions
    # status = Column(Enum(ScriptStatus), default=ScriptStatus.DRAFT)
    status = Column(String(20), default="DRAFT") 
    has_mp3 = Column(Boolean, default=False)
    is_editable = Column(Boolean, default=True)
    
    # Generation Metadata
    generation_prompt = Column(Text)  # Store the prompt used for AI generation
    generation_model = Column(String(50))  # gpt-4, gpt-3.5-turbo, etc.
    generation_temperature = Column(DECIMAL(3,2))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="scripts")
    persona = relationship("ScriptPersona", back_populates="scripts")
    mp3_files = relationship("MP3File", back_populates="script", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Script {self.id}: {self.title[:50]}...>"
    
    @property
    def can_edit(self):
        """Check if script can be edited (no MP3 files)"""
        return not self.has_mp3

    @property
    def status_enum(self):
        """Get status as enum if possible"""
        try:
            return MP3Status(self.status)
        except ValueError:
            return None     
    @property
    def is_completed(self):
        """Check if MP3 generation is completed"""
        return self.status == "completed"                   

    @property
    def is_processing(self):
        """Check if MP3 generation is in progress"""
        return self.status == "processing"

    @property
    def is_failed(self):
        """Check if MP3 generation failed"""
        return self.status == "failed"

    @property
    def persona_name(self):
        """Get persona name if exists"""
        return self.persona.name if self.persona else None
    
    @property
    def word_count(self):
        """Count words in content"""
        return len(self.content.split()) if self.content else 0
    
    @property
    def estimated_speech_duration(self):
        """Estimate speech duration (150 words per minute average)"""
        if self.duration_estimate:
            return self.duration_estimate
        # Estimate: 150 words per minute = 2.5 words per second
        return int(self.word_count / 2.5) if self.word_count > 0 else 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "product_id": self.product_id,
            "title": self.title,
            "content": self.content,
            "script_type": self.script_type.value,
            "persona_id": self.persona_id,
            "persona_name": self.persona_name,
            "language": self.language,
            "target_emotion": self.target_emotion,
            "tone": self.tone,
            "call_to_action": self.call_to_action,
            "duration_estimate": self.duration_estimate,
            "estimated_speech_duration": self.estimated_speech_duration,
            "status": self.status,
            "has_mp3": self.has_mp3,
            "is_editable": self.is_editable,
            "can_edit": self.can_edit,
            "word_count": self.word_count,
            "generation_model": self.generation_model,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "mp3_count": len(self.mp3_files) if self.mp3_files else 0
        }

class MP3File(Base):
    """MP3 file model for script audio"""
    __tablename__ = "mp3_files"
    
    # Basic Information
    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Audio Details
    duration = Column(DECIMAL(8,2))  # Duration in seconds
    file_size = Column(Integer)  # File size in bytes
    voice_persona_id = Column(Integer, ForeignKey("voice_personas.id"), nullable=True)
    
    # TTS Details
    tts_provider = Column(String(50))  # edge, google, elevenlabs
    voice_settings = Column(JSON)  # Store voice parameters
    
    # Quality and Status
    quality_rating = Column(Integer, default=0)  # 1-5 stars
    status = Column(String(20), default="processing")   
    
    # Generation Metadata
    generation_time = Column(DECIMAL(6,2))  # Time taken to generate in seconds
    error_message = Column(Text)  # Store error if generation failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    script = relationship("Script", back_populates="mp3_files")
    voice_persona = relationship("VoicePersona", back_populates="mp3_files")
    
    def __repr__(self):
        return f"<MP3File {self.id}: {self.filename}>"
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    @property
    def web_url(self):
        """Get web-accessible URL"""
        return f"/static/audio/{self.filename}"

    @property
    def is_completed(self):
        """Check if MP3 generation is completed"""
        return self.status == "completed"

    @property
    def is_processing(self):
        """Check if MP3 generation is in progress"""
        return self.status == "processing"

    @property
    def is_failed(self):
        """Check if MP3 generation failed"""
        return self.status == "failed"  
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
        "id": self.id,
        "script_id": self.script_id,
        "filename": self.filename,
        "file_path": self.file_path,
        "web_url": self.web_url,
        "duration": float(self.duration) if self.duration else None,
        "file_size": self.file_size,
        "file_size_mb": self.file_size_mb,
        "voice_persona_id": self.voice_persona_id,
        "tts_provider": self.tts_provider,
        "voice_settings": self.voice_settings or {},
        "quality_rating": self.quality_rating,
        "status": self.status,  # ใช้ string แทน enum
        # "is_completed": self.is_completed,
        # "is_processing": self.is_processing,
        # "is_failed": self.is_failed,
        "is_completed": self.status == "completed",
        "is_processing": self.status == "processing", 
        "is_failed": self.status == "failed",
        "generation_time": float(self.generation_time) if self.generation_time else None,
        "error_message": self.error_message,
        "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Video(Base):
    """Video model for product videos"""
    __tablename__ = "videos"
    
    # Basic Information
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Video Details
    duration = Column(DECIMAL(8,2))  # Duration in seconds
    file_size = Column(Integer)  # File size in bytes
    resolution = Column(String(20))  # 1920x1080, 1280x720, etc.
    video_type = Column(Enum(VideoType), default=VideoType.BACKGROUND)
    
    # Media
    thumbnail_path = Column(String(500))
    
    # Status
    status = Column(String(20), default="processing")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="videos")
    
    def __repr__(self):
        return f"<Video {self.id}: {self.title}>"
    
    @property
    def file_size_mb(self):
        """Get file size in MB"""
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0
    
    @property
    def web_url(self):
        """Get web-accessible URL"""
        return f"/uploads/videos/{self.filename}"
        
    @property
    def is_completed(self):
        """Check if video processing is completed"""
        return self.status == "completed"

    @property
    def is_processing(self):
        """Check if video processing is in progress"""
        return self.status == "processing"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
        "id": self.id,
        "product_id": self.product_id,
        "title": self.title,
        "filename": self.filename,
        "file_path": self.file_path,
        "web_url": self.web_url,
        "duration": float(self.duration) if self.duration else None,
        "file_size": self.file_size,
        "file_size_mb": self.file_size_mb,
        "resolution": self.resolution,
        "video_type": self.video_type.value if hasattr(self.video_type, 'value') else self.video_type,
        "thumbnail_path": self.thumbnail_path,
        "status": self.status,  # ใช้ string แทน enum
        # "is_completed": self.is_completed,
        # "is_processing": self.is_processing,
        "is_completed": self.status == "completed",
        "is_processing": self.status == "processing",
        "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ScriptPersona(Base):
    """Script persona model for AI script generation"""
    __tablename__ = "script_personas"
    
    # Basic Information
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # Persona Characteristics
    personality_traits = Column(JSON)  # ["enthusiastic", "confident", "persuasive"]
    speaking_style = Column(String(100))  # "Fast-paced, exciting"
    target_audience = Column(String(255))  # "Young adults, impulse buyers"
    
    # AI Prompting
    system_prompt = Column(Text, nullable=False)  # Main system prompt
    sample_phrases = Column(JSON)  # Example phrases this persona would use
    tone_guidelines = Column(Text)  # Guidelines for tone and mood
    do_say = Column(JSON)  # Phrases to encourage
    dont_say = Column(JSON)  # Phrases to avoid
    
    # Emotional Ranges
    default_emotion = Column(String(50), default="professional")
    available_emotions = Column(JSON)  # ["excited", "calm", "confident"]
    
    # Template Structure
    intro_template = Column(Text)  # Template for opening
    body_template = Column(Text)  # Template for main content
    cta_template = Column(Text)  # Template for call-to-action
    
    # Settings
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    # Usage Statistics
    usage_count = Column(Integer, default=0)
    success_rate = Column(DECIMAL(5,2), default=0.0)  # Percentage of successful generations
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scripts = relationship("Script", back_populates="persona")
    
    def __repr__(self):
        return f"<ScriptPersona {self.id}: {self.name}>"
    
    @property
    def traits_list(self):
        """Get personality traits as list"""
        return self.personality_traits or []
    
    @property
    def emotions_list(self):
        """Get available emotions as list"""
        return self.available_emotions or ["professional", "friendly", "excited"]
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality_traits": self.personality_traits or [],
            "speaking_style": self.speaking_style,
            "target_audience": self.target_audience,
            "system_prompt": self.system_prompt,
            "sample_phrases": self.sample_phrases or [],
            "tone_guidelines": self.tone_guidelines,
            "do_say": self.do_say or [],
            "dont_say": self.dont_say or [],
            "default_emotion": self.default_emotion,
            "available_emotions": self.available_emotions or [],
            "intro_template": self.intro_template,
            "body_template": self.body_template,
            "cta_template": self.cta_template,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "usage_count": self.usage_count,
            "success_rate": float(self.success_rate) if self.success_rate else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class VoicePersona(Base):
    """Voice persona model for TTS generation"""
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