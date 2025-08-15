# app/models/script.py
"""
Script model for AI Live Commerce Platform
Handles script content, AI generation metadata, and script lifecycle
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Enum, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import ScriptType, ScriptStatus, MP3Status

class Script(Base):
    """
    Script model for product scripts
    
    Responsibilities:
    - Store script content and metadata
    - Track AI generation parameters
    - Manage script lifecycle (draft -> approved -> archived)
    - Calculate duration estimates
    - Handle relationships with personas and MP3 files
    """
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