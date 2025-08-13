from sqlalchemy import Column, String, Text, ForeignKey, Enum, Float, DateTime, Integer, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import enum

class PlatformType(enum.Enum):
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    SHOPEE = "shopee"
    LAZADA = "lazada"
    WEBSITE = "website"

class MessageIntent(enum.Enum):
    GREETING = "greeting"
    QUESTION = "question"
    PURCHASE = "purchase"
    COMPLAINT = "complaint"
    GENERAL = "general"

class ChatMessage(Base):
    """Chat messages from live streams"""
    __tablename__ = "chat_messages"
    
    # Primary key - ต้องมี!
    id = Column(Integer, primary_key=True, index=True)
    
    # Platform info
    platform = Column(Enum(PlatformType), nullable=False, index=True)
    platform_user_id = Column(String)
    platform_username = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # AI Response
    ai_response = Column(Text)
    response_time_ms = Column(Float)
    intent = Column(Enum(MessageIntent))
    sentiment_score = Column(Float)  # -1 to 1
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    
    # Session tracking
    session_id = Column(String, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships (will be added when User model is ready)
    # user = relationship("User", backref="chat_messages")
    # product = relationship("Product", backref="related_chats")
    
    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform.value,
            "platform_user_id": self.platform_user_id,
            "platform_username": self.platform_username,
            "message": self.message,
            "ai_response": self.ai_response,
            "response_time_ms": self.response_time_ms,
            "intent": self.intent.value if self.intent else None,
            "sentiment_score": self.sentiment_score,
            "user_id": self.user_id,
            "product_id": self.product_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ChatSession(Base):
    """Chat sessions for live streams"""
    __tablename__ = "chat_sessions"
    
    # Primary key - ต้องมี!
    id = Column(Integer, primary_key=True, index=True)
    
    # Platform info
    platform = Column(Enum(PlatformType), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Session metrics
    total_messages = Column(Integer, default=0)
    total_ai_responses = Column(Integer, default=0)
    purchase_intents = Column(Integer, default=0)
    products_mentioned = Column(JSON, default=lambda: [])
    
    # Live stream info
    stream_title = Column(String)
    stream_url = Column(String)
    viewer_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships (will be added when User model is ready)
    # user = relationship("User", backref="chat_sessions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform.value,
            "user_id": self.user_id,
            "total_messages": self.total_messages,
            "total_ai_responses": self.total_ai_responses,
            "purchase_intents": self.purchase_intents,
            "products_mentioned": self.products_mentioned or [],
            "stream_title": self.stream_title,
            "stream_url": self.stream_url,
            "viewer_count": self.viewer_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None
        }