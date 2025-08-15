# app/models/script_persona.py
"""
Script persona model for AI Live Commerce Platform
Handles AI script generation personas and their characteristics
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class ScriptPersona(Base):
    """
    Script persona model for AI script generation
    
    Responsibilities:
    - Define personality traits and speaking styles
    - Store AI prompting templates and guidelines
    - Manage emotional ranges and tone settings
    - Track usage statistics and success rates
    - Provide template structures for script generation
    """
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