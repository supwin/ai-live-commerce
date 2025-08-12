from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
import uuid

class BaseModel:
    """Base model with common fields"""
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
