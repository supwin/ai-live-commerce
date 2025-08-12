from sqlalchemy import Column, String, Float, Integer, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import BaseModel


class Product(Base, BaseModel):
    __tablename__ = "products"
    
    name = Column(String, nullable=False, index=True)
    price = Column(Float, nullable=False)
    description = Column(String)
    features = Column(JSON, default=[])
    stock = Column(Integer, default=0)
    sku = Column(String, unique=True, index=True)
    category = Column(String, index=True)
    images = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", backref="products")
    scripts = relationship("ProductScript", back_populates="product", cascade="all, delete-orphan")
    
    # Analytics
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    sales = Column(Integer, default=0)
    
