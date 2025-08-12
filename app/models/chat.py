from sqlalchemy import Column, String, Text, ForeignKey, Enum, Float, DateTime, Integer, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel
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

class ChatMessage(Base, BaseModel):
    __tablename__ = "chat_messages"
    
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
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", backref="chat_messages")
    
    product_id = Column(String, ForeignKey("products.id"), nullable=True)
    product = relationship("Product", backref="related_chats")
    
    # Session tracking
    session_id = Column(String, index=True)
    
class ChatSession(Base, BaseModel):
    __tablename__ = "chat_sessions"
    
    platform = Column(Enum(PlatformType), nullable=False)
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", backref="chat_sessions")
    
    # Session metrics
    total_messages = Column(Integer, default=0)
    total_ai_responses = Column(Integer, default=0)
    purchase_intents = Column(Integer, default=0)
    products_mentioned = Column(JSON, default=[])
    
    # Live stream info
    stream_title = Column(String)
    stream_url = Column(String)
    viewer_count = Column(Integer, default=0)
    
    ended_at = Column(DateTime(timezone=True), nullable=True)
