#app/models/product.py

from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class ProductStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

class Product(Base):
    __tablename__ = "products"
    
    # Basic Information - เปลี่ยนจาก String UUID เป็น Integer
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Pricing Information
    price = Column(DECIMAL(10, 2), nullable=False)
    original_price = Column(DECIMAL(10, 2))
    discount_percentage = Column(Integer, default=0)
    
    # Product Details
    category = Column(String(100))
    brand = Column(String(100))
    tags = Column(JSON)  # ["electronics", "smartphone", "android"]
    stock_quantity = Column(Integer, default=0)
    weight = Column(DECIMAL(8, 2))  # kg
    dimensions = Column(String(100))  # "15.5 x 7.5 x 0.8 cm"
    
    # Product Variants
    color_options = Column(JSON)  # ["black", "white", "blue"]
    size_options = Column(JSON)   # ["S", "M", "L", "XL"]
    
    # Marketing Information (สำหรับ AI Script Generation)
    key_features = Column(JSON)  # ["4K camera", "Fast charging", "Waterproof"]
    target_audience = Column(String(255))  # "Young professionals, Tech enthusiasts"
    use_cases = Column(JSON)  # ["Photography", "Gaming", "Business"]
    selling_points = Column(JSON)  # ["Best price", "Premium quality", "Fast delivery"]
    promotion_text = Column(String(500))  # "Limited time offer! 50% off this week only!"
    
    # Additional Information
    warranty_info = Column(String(255))
    shipping_info = Column(String(255))
    
    # Status and Media
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE)
    thumbnail_url = Column(String(500))
    images = Column(JSON)  # ["image1.jpg", "image2.jpg"]
    
    # SEO
    meta_title = Column(String(255))
    meta_description = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    scripts = relationship("Script", back_populates="product", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product {self.sku}: {self.name}>"
    
    @property
    def is_on_sale(self):
        """Check if product is currently on sale"""
        return self.discount_percentage > 0
    
    @property
    def sale_price(self):
        """Calculate sale price if on discount"""
        if self.discount_percentage > 0:
            return float(self.price) * (1 - self.discount_percentage / 100)
        return float(self.price)
    
    @property
    def total_scripts(self):
        """Get total number of scripts for this product"""
        return len(self.scripts)
    
    @property
    def total_mp3s(self):
        """Get total number of MP3 files for this product"""
        return sum(1 for script in self.scripts for mp3 in script.mp3_files)
    
    @property
    def total_videos(self):
        """Get total number of videos for this product"""
        return len(self.videos)
    
    @property
    def has_content_ready(self):
        """Check if product has scripts and MP3s ready for live streaming"""
        return self.total_scripts > 0 and self.total_mp3s > 0
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "sku": self.sku,
            "name": self.name,
            "description": self.description,
            "price": float(self.price) if self.price else 0.0,
            "original_price": float(self.original_price) if self.original_price else None,
            "discount_percentage": self.discount_percentage,
            "sale_price": self.sale_price,
            "is_on_sale": self.is_on_sale,
            "category": self.category,
            "brand": self.brand,
            "tags": self.tags or [],
            "stock_quantity": self.stock_quantity,
            "weight": float(self.weight) if self.weight else None,
            "dimensions": self.dimensions,
            "color_options": self.color_options or [],
            "size_options": self.size_options or [],
            "key_features": self.key_features or [],
            "target_audience": self.target_audience,
            "use_cases": self.use_cases or [],
            "selling_points": self.selling_points or [],
            "promotion_text": self.promotion_text,
            "warranty_info": self.warranty_info,
            "shipping_info": self.shipping_info,
            "status": self.status.value,
            "thumbnail_url": self.thumbnail_url,
            "images": self.images or [],
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "total_scripts": self.total_scripts,
            "total_mp3s": self.total_mp3s,
            "total_videos": self.total_videos,
            "has_content_ready": self.has_content_ready,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }