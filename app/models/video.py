# app/models/video.py
"""
Video model for AI Live Commerce Platform
Handles video file storage, metadata, and processing status
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base
from .enums import VideoType

class Video(Base):
    """
    Video model for product videos
    
    Responsibilities:
    - Store video file metadata and paths
    - Track video processing status
    - Manage video types and categories
    - Handle thumbnail associations
    - Provide file size calculations and URLs
    """
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
            "status": self.status,
            "is_completed": self.status == "completed",
            "is_processing": self.status == "processing",
            "created_at": self.created_at.isoformat() if self.created_at else None
        }