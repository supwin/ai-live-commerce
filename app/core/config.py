# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import EmailStr, field_validator
from typing import List, Dict, Optional, Any
from functools import lru_cache
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "AI Live Commerce Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_live_commerce.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Security
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 150
    
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE: str = "Bella"
    
    # TTS Settings
    TTS_PROVIDER: str = "edge"  # "edge", "elevenlabs", "google"
    TTS_VOICE_TH: str = "th-TH-PremwadeeNeural"
    TTS_VOICE_EN: str = "en-US-AriaNeural"
    TTS_RATE: float = 1.0
    TTS_PITCH: float = 1.0
    
    # OBS Settings
    OBS_WEBSOCKET_HOST: str = "localhost"
    OBS_WEBSOCKET_PORT: int = 4455
    OBS_WEBSOCKET_PASSWORD: str = ""
    OBS_AUTO_RECONNECT: bool = True
    OBS_RECONNECT_INTERVAL: int = 5
    
    # Platform Settings
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_VERIFY_TOKEN: str = "ai_live_commerce_verify"
    
    TIKTOK_API_KEY: Optional[str] = None
    TIKTOK_API_SECRET: Optional[str] = None
    
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: Path = Path("./uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".mp4", ".gif"]
    
    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("./logs")
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60  # seconds
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[EmailStr] = None
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY must be set")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v
    
    @field_validator("UPLOAD_DIR", "LOG_DIR")
    @classmethod
    def create_directories(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# app/core/exceptions.py
from typing import Any, Optional, Dict

class AppException(Exception):
    """Base application exception"""
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(AppException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            status_code=401,
            details=details
        )

class AuthorizationError(AppException):
    """Authorization failed"""
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            code="AUTHZ_ERROR",
            status_code=403,
            details=details
        )

class ValidationError(AppException):
    """Data validation error"""
    def __init__(self, message: str, field: str = None, details: Optional[Dict] = None):
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )

class NotFoundError(AppException):
    """Resource not found"""
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource} not found"
        details = {"resource": resource}
        if identifier:
            details["id"] = str(identifier)
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=404,
            details=details
        )

class PlatformError(AppException):
    """Platform integration error"""
    def __init__(self, platform: str, message: str, details: Optional[Dict] = None):
        details = details or {}
        details["platform"] = platform
        super().__init__(
            message=f"{platform}: {message}",
            code="PLATFORM_ERROR",
            status_code=503,
            details=details
        )

class AIServiceError(AppException):
    """AI service error"""
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        details = details or {}
        details["service"] = service
        super().__init__(
            message=f"AI Service Error ({service}): {message}",
            code="AI_SERVICE_ERROR",
            status_code=503,
            details=details
        )

# app/utils/validators.py
import re
from typing import Any, Dict, List
from pydantic import BaseModel, Field, validator
import json

class ProductValidator(BaseModel):
    """Product data validator"""
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    description: str = Field(..., max_length=1000)
    features: List[str] = Field(default_factory=list)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Product name cannot be empty')
        return v.strip()
    
    @validator('features')
    def validate_features(cls, v):
        return [f.strip() for f in v if f.strip()]

class PlatformCredentialsValidator:
    """Validate platform credentials"""
    
    @staticmethod
    def validate_facebook(credentials: Dict[str, Any]) -> bool:
        required = ['access_token', 'page_id']
        return all(k in credentials and credentials[k] for k in required)
    
    @staticmethod
    def validate_tiktok(credentials: Dict[str, Any]) -> bool:
        required = ['session_id']  # TikTok session cookie
        return all(k in credentials and credentials[k] for k in required)
    
    @staticmethod
    def validate_youtube(credentials: Dict[str, Any]) -> bool:
        required = ['api_key', 'channel_id']
        return all(k in credentials and credentials[k] for k in required)

class MessageValidator:
    """Validate and sanitize chat messages"""
    
    @staticmethod
    def sanitize_message(message: str) -> str:
        """Remove harmful content from messages"""
        # Remove HTML/Script tags
        message = re.sub(r'<[^>]+>', '', message)
        # Remove excessive whitespace
        message = ' '.join(message.split())
        # Limit length
        return message[:500]
    
    @staticmethod
    def is_spam(message: str, spam_keywords: List[str] = None) -> bool:
        """Check if message is spam"""
        default_spam = ['bit.ly', 'tinyurl', 'click here', 'buy now', 'limited time']
        spam_keywords = spam_keywords or default_spam
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in spam_keywords)
    
    @staticmethod
    def detect_language(message: str) -> str:
        """Simple language detection"""
        thai_chars = re.findall(r'[\u0E00-\u0E7F]', message)
        english_chars = re.findall(r'[a-zA-Z]', message)
        
        if len(thai_chars) > len(english_chars):
            return 'th'
        return 'en'

# app/utils/helpers.py
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json

def generate_session_id() -> str:
    """Generate unique session ID"""
    timestamp = datetime.utcnow().timestamp()
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    return hashlib.sha256(f"{timestamp}{random_str}".encode()).hexdigest()[:32]

def format_price(price: float, currency: str = "THB") -> str:
    """Format price with currency"""
    currencies = {
        "THB": "฿",
        "USD": "$",
        "EUR": "€"
    }
    symbol = currencies.get(currency, currency)
    return f"{symbol}{price:,.2f}"

def calculate_response_time(start_time: datetime) -> float:
    """Calculate response time in milliseconds"""
    delta = datetime.utcnow() - start_time
    return delta.total_seconds() * 1000

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def parse_time_duration(duration_str: str) -> timedelta:
    """Parse duration string (e.g., '1h30m', '45m', '2h')"""
    pattern = re.compile(r'(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
    match = pattern.match(duration_str)
    
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}")
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result