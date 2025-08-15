# app/models/mp3.py
"""
MP3 file model for AI Live Commerce Platform
Handles audio file generation, storage, and metadata
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base

class MP3File(Base):
    """
    MP3 file model for script audio
    
    Responsibilities:
    - Store audio file metadata and paths
    - Track TTS generation details
    - Manage file status and quality ratings
    - Handle voice persona relationships
    - Provide file size calculations and URLs
    """
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
            "status": self.status,
            "is_completed": self.status == "completed",
            "is_processing": self.status == "processing", 
            "is_failed": self.status == "failed",
            "generation_time": float(self.generation_time) if self.generation_time else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }