# app/api/v1/dependencies.py
"""
Fixed Dependencies และ Imports สำหรับ Dashboard API
แก้ไขปัญหา 500 error จากการขาด imports
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Any

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

# Database และ Models - ตรวจสอบ path ให้ถูกต้อง
try:
    from app.core.database import get_db
    print("✅ Database connection imported successfully")
except ImportError as e:
    print(f"❌ Failed to import database: {e}")
    # Fallback - สร้าง mock function
    def get_db():
        raise HTTPException(status_code=500, detail="Database connection not available")

try:
    from app.models.product import Product, ProductStatus
    print("✅ Product models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Product models: {e}")
    Product = None
    ProductStatus = None

try:
    from app.models import (
        Script, MP3File, Video, ScriptPersona, VoicePersona, 
        ScriptType, ScriptStatus
    )
    print("✅ Script models imported successfully")
except ImportError as e:
    print(f"❌ Failed to import Script models: {e}")
    Script = MP3File = Video = ScriptPersona = VoicePersona = None
    ScriptType = ScriptStatus = None

try:
    from app.models.user import User
    print("✅ User model imported successfully")
except ImportError as e:
    print(f"❌ Failed to import User model: {e}")
    User = None

# Services - จัดการ import ที่อาจมีปัญหา
def get_ai_script_service():
    """ดึง AI Script Service พร้อมจัดการ error"""
    try:
        from app.services.ai_script_service import ai_script_service
        print("✅ AI Script Service imported successfully")
        return ai_script_service
    except ImportError as e:
        print(f"⚠️ Could not import AI Script Service: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Error loading AI Script Service: {e}")
        return None

def get_tts_service():
    """ดึง TTS Service พร้อม fallback"""
    try:
        from app.services.tts import enhanced_tts_service as tts_service
        print("✅ Enhanced TTS Service imported successfully")
        return tts_service
    except ImportError as e:
        print(f"⚠️ Could not import Enhanced TTS Service: {e}")
        try:
            from app.services.tts_service import tts_service
            print("✅ Fallback to basic TTS Service")
            return tts_service
        except ImportError as e2:
            print(f"❌ Could not import any TTS Service: {e2}")
            return None
    except Exception as e:
        print(f"⚠️ Error loading TTS Service: {e}")
        return None

def get_file_handler():
    """ดึง File Handler พร้อม mock fallback"""
    try:
        from app.utils.file_handler import file_handler
        print("✅ File Handler imported successfully")
        return file_handler
    except ImportError as e:
        print(f"⚠️ Could not import File Handler: {e}")
        
        # สร้าง mock file handler
        class MockFileHandler:
            def save_uploaded_file(self, file, subdirectory: str = ""):
                return f"/uploads/{subdirectory}/{file.filename}", file.filename
        
        print("✅ Using Mock File Handler")
        return MockFileHandler()

def get_custom_exceptions():
    """ดึง Custom Exceptions พร้อม fallback"""
    try:
        from app.core.exceptions import ValidationError, NotFoundError
        print("✅ Custom Exceptions imported successfully")
        return ValidationError, NotFoundError
    except ImportError as e:
        print(f"⚠️ Could not import custom exceptions: {e}")
        
        # สร้าง basic exception classes
        class ValidationError(Exception):
            def __init__(self, message: str, field: str = None):
                self.message = message
                self.field = field
                super().__init__(message)
        
        class NotFoundError(Exception):
            def __init__(self, message: str):
                self.message = message
                super().__init__(message)
        
        print("✅ Using fallback Exception classes")
        return ValidationError, NotFoundError

# Initialize services
ai_script_service = get_ai_script_service()
tts_service = get_tts_service()
file_handler = get_file_handler()
ValidationError, NotFoundError = get_custom_exceptions()

# Helper functions พร้อมการตรวจสอบ models
async def validate_product_exists(product_id: int, db: Session):
    """ตรวจสอบว่าสินค้ามีอยู่จริง"""
    if not Product:
        raise HTTPException(status_code=500, detail="Product model not available")
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

async def validate_script_exists(script_id: int, db: Session):
    """ตรวจสอบว่าสคริปต์มีอยู่จริง"""
    if not Script:
        raise HTTPException(status_code=500, detail="Script model not available")
    
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script

async def validate_persona_exists(persona_id: int, db: Session, persona_type: str = "script"):
    """ตรวจสอบว่า persona มีอยู่จริง"""
    if persona_type == "script":
        if not ScriptPersona:
            raise HTTPException(status_code=500, detail="ScriptPersona model not available")
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == persona_id).first()
    elif persona_type == "voice":
        if not VoicePersona:
            raise HTTPException(status_code=500, detail="VoicePersona model not available")
        persona = db.query(VoicePersona).filter(VoicePersona.id == persona_id).first()
    else:
        raise HTTPException(status_code=400, detail="Invalid persona type")
    
    if not persona:
        raise HTTPException(status_code=404, detail=f"{persona_type.title()} persona not found")
    return persona

def check_ai_service_availability():
    """ตรวจสอบสถานะ AI Service"""
    if not ai_script_service:
        raise HTTPException(
            status_code=503, 
            detail="AI Script Service is not available. Please check OpenAI API configuration."
        )
    return ai_script_service

def check_tts_service_availability():
    """ตรวจสอบสถานะ TTS Service"""
    if not tts_service:
        raise HTTPException(
            status_code=503,
            detail="TTS Service is not available. Please check TTS configuration."
        )
    return tts_service

def check_models_availability():
    """ตรวจสอบว่า models ทั้งหมดโหลดได้"""
    missing_models = []
    
    if not Product:
        missing_models.append("Product")
    if not Script:
        missing_models.append("Script")
    if not ScriptPersona:
        missing_models.append("ScriptPersona")
    if not VoicePersona:
        missing_models.append("VoicePersona")
    
    if missing_models:
        raise HTTPException(
            status_code=500,
            detail=f"Missing models: {', '.join(missing_models)}. Please check database configuration."
        )
    
    return True

# Utility functions
def calculate_duration_estimate(content: str) -> int:
    """คำนวณเวลาโดยประมาณจากเนื้อหา"""
    try:
        word_count = len(content.split())
        return max(30, int(word_count / 2.5))  # 2.5 คำต่อวินาที
    except Exception:
        return 60  # fallback

def get_date_range(days: int) -> datetime:
    """คำนวณช่วงเวลาย้อนหลัง"""
    try:
        return datetime.utcnow() - timedelta(days=days)
    except Exception:
        return datetime.utcnow() - timedelta(days=30)  # fallback

def safe_file_delete(file_path: str) -> bool:
    """ลบไฟล์อย่างปลอดภัย"""
    if not file_path:
        return False
        
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Deleted file: {file_path}")
            return True
    except Exception as e:
        print(f"⚠️ Failed to delete file {file_path}: {e}")
    
    return False

# Constants
SUPPORTED_TTS_PROVIDERS = ["edge", "google", "elevenlabs"]
SUPPORTED_EMOTIONS = [
    "professional", "excited", "friendly", "confident", 
    "energetic", "calm", "urgent", "cheerful", "serious", "gentle"
]
DEFAULT_VOICE_CONFIGS = {
    "edge": "th-TH-PremwadeeNeural",
    "elevenlabs": "pNInz6obpgDQGcFmaJgB",
    "google": "th-TH-Standard-A"
}

# Error handlers with better diagnostics
def handle_database_error(e: Exception, operation: str):
    """จัดการ database errors พร้อม detailed logging"""
    error_msg = f"Database error in {operation}: {str(e)}"
    print(f"❌ {error_msg}")
    
    # Log additional debug info
    print(f"🔍 Debug info:")
    print(f"   Operation: {operation}")
    print(f"   Error type: {type(e).__name__}")
    print(f"   Models available: Product={Product is not None}, Script={Script is not None}")
    
    raise HTTPException(
        status_code=500, 
        detail=f"Database error in {operation}. Please check server logs for details."
    )

def handle_service_error(e: Exception, service: str):
    """จัดการ service errors พร้อม detailed logging"""
    error_msg = f"Service error in {service}: {str(e)}"
    print(f"❌ {error_msg}")
    
    # Log service status
    print(f"🔍 Service status:")
    print(f"   Service: {service}")
    print(f"   AI Service: {ai_script_service is not None}")
    print(f"   TTS Service: {tts_service is not None}")
    
    raise HTTPException(
        status_code=500, 
        detail=f"Service error in {service}. Please check service configuration."
    )

# Startup diagnostic
def run_startup_diagnostics():
    """รันการตรวจสอบเบื้องต้นเมื่อเริ่มระบบ"""
    print("\n🚀 Dashboard API Dependencies Startup Diagnostics:")
    print("=" * 50)
    
    # Check models
    print(f"📊 Models Status:")
    print(f"   Product: {'✅' if Product else '❌'}")
    print(f"   Script: {'✅' if Script else '❌'}")
    print(f"   ScriptPersona: {'✅' if ScriptPersona else '❌'}")
    print(f"   VoicePersona: {'✅' if VoicePersona else '❌'}")
    
    # Check services
    print(f"🛠️ Services Status:")
    print(f"   AI Script Service: {'✅' if ai_script_service else '❌'}")
    print(f"   TTS Service: {'✅' if tts_service else '❌'}")
    print(f"   File Handler: {'✅' if file_handler else '❌'}")
    
    # Overall status
    models_ok = all([Product, Script, ScriptPersona, VoicePersona])
    services_ok = all([tts_service, file_handler])  # AI service optional
    
    overall_status = "✅ READY" if models_ok else "⚠️ DEGRADED"
    print(f"\n🎯 Overall Status: {overall_status}")
    
    if not models_ok:
        print("⚠️ Some models failed to load - certain endpoints may not work")
    if not services_ok:
        print("⚠️ Some services failed to load - functionality may be limited")
    
    print("=" * 50)
    return models_ok and services_ok

# เรียกใช้ diagnostics เมื่อ import
try:
    run_startup_diagnostics()
except Exception as e:
    print(f"❌ Diagnostics failed: {e}")