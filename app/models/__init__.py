# Import Base first
from .base import Base

# Import all working models
from .product import Product
from .script import (
    Script,
    MP3File, 
    Video, 
    ScriptPersona, 
    VoicePersona
)
from .chat import ChatMessage, ChatSession
from .script import Script, MP3File, Video, ScriptPersona, VoicePersona

# Import User if fixed
try:
    from .user import User
    user_available = True
except ImportError:
    user_available = False

# Make models available
if user_available:
    __all__ = [
        "Base",
        "User",
        "Product",
        "Script",
        "MP3File",
        "Video",
        "ScriptPersona",
        "VoicePersona",
        "ChatMessage",
        "ChatSession"
    ]
else:
    __all__ = [
        "Base",
        "Product",
        "Script",
        "MP3File",
        "Video",
        "ScriptPersona",
        "VoicePersona",
        "ChatMessage",
        "ChatSession"
    ]