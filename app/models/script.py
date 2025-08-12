# app/models/script.py
"""
Script model for storing product presentation scripts
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.core.database import Base

class ProductScript(Base, BaseModel):
    """Product presentation script model"""
    __tablename__ = "product_scripts"
    
    product_id = Column(String, ForeignKey("products.id"), nullable=False)
    title = Column(String(200), nullable=False)  # e.g., "แบบกระตุ้นความต้องการ"
    content = Column(Text, nullable=False)  # Script content
    script_type = Column(String(50), nullable=False)  # e.g., "emotional", "informative", "interactive"
    usage_count = Column(Integer, default=0)  # How many times used
    is_active = Column(Boolean, default=True)
    
    # Relationship
    product = relationship("Product", back_populates="scripts")
    
    def __repr__(self):
        return f"<ProductScript {self.title} for Product {self.product_id}>"