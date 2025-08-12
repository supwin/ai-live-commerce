# app/models/__init__.py
"""
Models package initialization
Import all models to ensure they're registered with SQLAlchemy
"""

from app.models.base import BaseModel
from app.models.user import User
from app.models.product import Product
from app.models.chat import ChatMessage, ChatSession
from app.models.script import ProductScript

__all__ = [
    'BaseModel',
    'User', 
    'Product',
    'ChatMessage',
    'ChatSession',
    'ProductScript'
]