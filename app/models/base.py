from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

# SQLAlchemy Base for all models
Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields - Abstract class"""
    __abstract__ = True
    
    # Note: ID field should be defined in each specific model
    # as Integer or String depending on requirements
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())