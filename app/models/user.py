from sqlalchemy import Column, String, Boolean, JSON
from app.core.database import Base
from app.models.base import BaseModel

class User(Base, BaseModel):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Platform credentials (encrypted)
    platform_credentials = Column(JSON, default={})
    
    # User preferences
    preferences = Column(JSON, default={
        "tts_voice": "th-TH-PremwadeeNeural",
        "ai_model": "gpt-4",
        "auto_response": True,
        "language": "th"
    })
