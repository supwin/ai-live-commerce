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
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True
    
    # OpenAI Configuration (MAIN SETTINGS)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"  # Changed default to more affordable model
    OPENAI_TEMPERATURE: float = 0.7
    OPENAI_MAX_TOKENS: int = 1500  # Increased for longer scripts
    OPENAI_TOP_P: float = 0.9
    OPENAI_FREQUENCY_PENALTY: float = 0.1
    OPENAI_PRESENCE_PENALTY: float = 0.1
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 2  # Reduced for better performance on 8GB RAM
    
    # Database
    DATABASE_URL: str = "sqlite:///./ai_live_commerce.db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False  # Set to True for SQL debugging
    
    # Security
    SECRET_KEY: str = "development_secret_key_ai_live_commerce_2025"
    ENCRYPTION_KEY: str = "SgJOc-ZTdTacmYi9fBBG2d-oNzXYD1S497zyVfQHocU="
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # TTS Settings
    TTS_PROVIDER: str = "edge"  # "edge", "elevenlabs", "google"
    TTS_VOICE_TH: str = "th-TH-PremwadeeNeural"
    TTS_VOICE_EN: str = "en-US-AriaNeural"
    TTS_RATE: float = 1.0
    TTS_PITCH: float = 1.0
    TTS_DEFAULT_LANGUAGE: str = "th"
    TTS_DEFAULT_PROVIDER: str = "edge"
    
    # ElevenLabs (Optional)
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE: str = "Bella"
    
    # Google TTS (Optional)
    GOOGLE_TTS_API_KEY: Optional[str] = None
    
    AZURE_SPEECH_KEY: Optional[str] = None
    AZURE_SPEECH_REGION: str = "southeastasia"
    MICROSOFT_SPEECH_KEY: Optional[str] = None
    MICROSOFT_SPEECH_REGION: str = "southeastasia"

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
    FACEBOOK_REDIRECT_URI: str = "http://localhost:8000/api/facebook/callback"
    FACEBOOK_API_VERSION: str = "v18.0"
    FACEBOOK_MOCK_MODE: str = "false"
    FACEBOOK_PAGE_ID: str = ""
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ""
    
    TIKTOK_API_KEY: Optional[str] = None
    TIKTOK_API_SECRET: Optional[str] = None
    
    YOUTUBE_API_KEY: Optional[str] = None
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: Path = Path("./frontend/uploads")
    STATIC_DIR: Path = Path("./frontend/static")
    AUDIO_DIR: Path = Path("./frontend/static/audio")
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".mp4", ".gif", ".mp3", ".wav"]
    
    # Cache
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 300  # 5 minutes
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: Path = Path("./logs")
    LOG_FILE: str = "logs/app.log"
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
    
    # Live Streaming Settings
    LIVE_DEFAULT_BITRATE: str = "4000000"
    LIVE_DEFAULT_RESOLUTION: str = "720p"
    LIVE_DEFAULT_FPS: str = "30"
    LIVE_MAX_DURATION: str = "3600"
    
    # Avatar Settings
    AVATAR_DEFAULT_VOICE: str = "th"
    AVATAR_DEFAULT_SPEED: str = "1.0"
    AVATAR_CACHE_SIZE: str = "100"
    
    # Other Settings
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"
    RELOAD: str = "true"
    
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        if not v or len(v) < 16:
            return "development_secret_key_ai_live_commerce_2025"
        return v
    
    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v):
        if v and not v.startswith('sk-'):
            print(f"⚠️ WARNING: OpenAI API key should start with 'sk-'")
        return v
    
    @field_validator("OPENAI_MODEL")
    @classmethod
    def validate_openai_model(cls, v):
        # List of commonly available models
        valid_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview"
        ]
        if v not in valid_models:
            print(f"⚠️ WARNING: Model '{v}' may not be available. Common models: {', '.join(valid_models[:3])}")
        return v
    
    @field_validator("OPENAI_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v):
        return max(0.0, min(2.0, float(v)))
    
    @field_validator("UPLOAD_DIR", "LOG_DIR", "STATIC_DIR", "AUDIO_DIR")
    @classmethod
    def create_directories(cls, v):
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string
            return [origin.strip() for origin in v.split(",")]
        return v
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration dictionary"""
        return {
            "api_key": self.OPENAI_API_KEY,
            "model": self.OPENAI_MODEL,
            "temperature": self.OPENAI_TEMPERATURE,
            "max_tokens": self.OPENAI_MAX_TOKENS,
            "top_p": self.OPENAI_TOP_P,
            "frequency_penalty": self.OPENAI_FREQUENCY_PENALTY,
            "presence_penalty": self.OPENAI_PRESENCE_PENALTY
        }
    
    def is_openai_configured(self) -> bool:
        """Check if OpenAI is properly configured"""
        return bool(
            self.OPENAI_API_KEY and 
            self.OPENAI_API_KEY.strip() and 
            self.OPENAI_API_KEY.startswith('sk-')
        )
    
    def get_tts_config(self) -> Dict[str, Any]:
        """Get TTS configuration dictionary"""
        return {
            "provider": self.TTS_PROVIDER,
            "voice_th": self.TTS_VOICE_TH,
            "voice_en": self.TTS_VOICE_EN,
            "rate": self.TTS_RATE,
            "pitch": self.TTS_PITCH,
            "language": self.TTS_DEFAULT_LANGUAGE
        }

    def is_elevenlabs_configured(self) -> bool:
        """ตรวจสอบว่า ElevenLabs API key ได้ถูกตั้งค่าแล้วหรือไม่"""
        configured = bool(self.ELEVENLABS_API_KEY and self.ELEVENLABS_API_KEY.strip())
        print(f"🔍 ElevenLabs check: {'✅ Configured' if configured else '❌ Missing'}")
        if configured:
            print(f"🔑 Key preview: {self.ELEVENLABS_API_KEY[:15]}...")
        return configured

    def is_azure_tts_configured(self) -> bool:
        """ตรวจสอบ Azure Speech Services configuration"""
        return bool(self.AZURE_SPEECH_KEY and self.AZURE_SPEECH_REGION)

    def is_google_tts_configured(self) -> bool:
        """ตรวจสอบ Google TTS configuration"""
        return bool(self.GOOGLE_TTS_API_KEY)

    def get_tts_providers_status(self) -> Dict[str, Any]:
        """ส่งคืนสถานะการตั้งค่า TTS providers ทั้งหมด"""
        return {
            "edge": {
                "configured": True,  # Microsoft Edge TTS ใช้ได้เสมอ
                "available": True,
                "type": "free",
                "note": "Built-in Microsoft Edge TTS"
            },
            "elevenlabs": {
                "configured": self.is_elevenlabs_configured(),
                "available": self.is_elevenlabs_configured(),
                "type": "premium",
                "api_key_length": len(self.ELEVENLABS_API_KEY) if self.ELEVENLABS_API_KEY else 0,
                "note": "Premium AI voices" if self.is_elevenlabs_configured() else "API key required"
            },
            "azure": {
                "configured": self.is_azure_tts_configured(),
                "available": self.is_azure_tts_configured(),
                "type": "enterprise",
                "region": self.AZURE_SPEECH_REGION,
                "note": "Enterprise TTS" if self.is_azure_tts_configured() else "API key required"
            },
            "google": {
                "configured": self.is_google_tts_configured(),
                "available": self.is_google_tts_configured(),
                "type": "standard",
                "note": "Google Cloud TTS" if self.is_google_tts_configured() else "API key required"
            },
            "basic": {
                "configured": True,
                "available": True,
                "type": "basic",
                "note": "Basic text-to-speech"
            }
        }

    def debug_tts_configuration(self) -> None:
        """Debug TTS configuration"""
        print("\n" + "=" * 50)
        print("🔍 TTS Configuration Debug")
        print("=" * 50)
        
        # ตรวจสอบ .env file
        env_file_exists = os.path.exists('.env')
        print(f"📁 .env file exists: {env_file_exists}")
        
        # ตรวจสอบ environment variables
        elevenlabs_env = os.getenv('ELEVENLABS_API_KEY')
        print(f"🌍 ELEVENLABS_API_KEY from environment: {'✅ Found' if elevenlabs_env else '❌ Not found'}")
        if elevenlabs_env:
            print(f"🔑 Environment key preview: {elevenlabs_env[:15]}...")
        
        # ตรวจสอบ settings object
        print(f"⚙️ Settings object key: {'✅ Loaded' if self.ELEVENLABS_API_KEY else '❌ Not loaded'}")
        if self.ELEVENLABS_API_KEY:
            print(f"🔑 Settings key preview: {self.ELEVENLABS_API_KEY[:15]}...")
        
        # ตรวจสอบการทำงานของ helper methods
        print(f"✅ is_elevenlabs_configured(): {self.is_elevenlabs_configured()}")
        
        # แสดงสถานะ providers ทั้งหมด
        print("\n📊 All TTS Providers Status:")
        providers_status = self.get_tts_providers_status()
        for provider, status in providers_status.items():
            icon = "✅" if status['available'] else "❌"
            print(f"   {icon} {provider}: {status['note']}")
        
        print("=" * 50 + "\n")    
        
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Utility functions
def validate_openai_setup() -> Dict[str, Any]:
    """Validate OpenAI setup and return status"""
    settings = get_settings()
    
    status = {
        "configured": False,
        "api_key_present": False,
        "api_key_valid_format": False,
        "model": settings.OPENAI_MODEL,
        "issues": []
    }
    
    # Check API key presence
    if settings.OPENAI_API_KEY:
        status["api_key_present"] = True
        
        # Check API key format
        if settings.OPENAI_API_KEY.startswith('sk-'):
            status["api_key_valid_format"] = True
            status["configured"] = True
        else:
            status["issues"].append("API key should start with 'sk-'")
    else:
        status["issues"].append("OPENAI_API_KEY not set in environment variables")
    
    # Check model
    if not settings.OPENAI_MODEL:
        status["issues"].append("OPENAI_MODEL not specified")
    
    return status


def print_startup_info():
    """Print configuration info at startup"""
    settings = get_settings()
    openai_status = validate_openai_setup()
    
    print("=" * 60)
    print("🤖 AI Live Commerce - Configuration Status")
    print("=" * 60)
    print(f"📱 App: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"🌐 Server: {settings.HOST}:{settings.PORT}")
    print(f"🗄️ Database: {settings.DATABASE_URL}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print("=" * 60)
    print("🧠 AI Configuration:")
    print(f"   OpenAI Configured: {'✅' if openai_status['configured'] else '❌'}")
    if openai_status['configured']:
        print(f"   Model: {settings.OPENAI_MODEL}")
        print(f"   Temperature: {settings.OPENAI_TEMPERATURE}")
        print(f"   Max Tokens: {settings.OPENAI_MAX_TOKENS}")
    else:
        print("   Issues:")
        for issue in openai_status['issues']:
            print(f"   - {issue}")
        print("   💡 AI script generation will use simulation mode")
    print("=" * 60)
    print("🎵 TTS Configuration:")
    print(f"   Default Provider: {settings.TTS_PROVIDER}")
    print(f"   Thai Voice: {settings.TTS_VOICE_TH}")
    print(f"   Language: {settings.TTS_DEFAULT_LANGUAGE}")
    
    # ✅ เพิ่มส่วนนี้ - แสดงสถานะ TTS providers
    print("\n🎤 TTS Providers Status:")
    providers_status = settings.get_tts_providers_status()
    for provider, status in providers_status.items():
        icon = "✅" if status['available'] else "❌"
        print(f"   {icon} {provider.capitalize()}: {status['note']}")
    
    print("=" * 60)
    
    # ✅ เรียก debug หาก debug mode เปิด
    if settings.DEBUG:
        settings.debug_tts_configuration()




