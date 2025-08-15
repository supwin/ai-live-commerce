# app/api/v1/endpoints/__init__.py
"""
Endpoints Package Initialization
รวมเส้นทาง API endpoints ทั้งหมด
"""

# Import all endpoint modules
from . import dashboard_stats
from . import products
from . import scripts
from . import mp3_generation
from . import personas
from . import analytics
from . import utilities

# Export for easy importing
__all__ = [
    "dashboard_stats",
    "products", 
    "scripts",
    "mp3_generation",
    "personas",
    "analytics",
    "utilities"
]

# Endpoint information for documentation
ENDPOINT_INFO = {
    "dashboard_stats": {
        "description": "สถิติและสถานะของ Dashboard",
        "endpoints": [
            "GET /stats - สถิติรวม",
            "GET /ai-status - สถานะ AI Service",
            "GET /system-health - สุขภาพระบบ",
            "GET /performance-metrics - เมตริกประสิทธิภาพ"
        ]
    },
    "products": {
        "description": "การจัดการสินค้า CRUD operations",
        "endpoints": [
            "GET /products - รายการสินค้า",
            "POST /products - สร้างสินค้าใหม่",
            "GET /products/{id} - ข้อมูลสินค้า",
            "PUT /products/{id} - อัปเดตสินค้า",
            "DELETE /products/{id} - ลบสินค้า",
            "GET /categories - หมวดหมู่สินค้า",
            "GET /brands - แบรนด์สินค้า"
        ]
    },
    "scripts": {
        "description": "การจัดการสคริปต์ AI และ Manual",
        "endpoints": [
            "GET /products/{id}/scripts - สคริปต์ของสินค้า",
            "POST /scripts/generate-ai - สร้างสคริปต์ด้วย AI",
            "POST /scripts/manual - สร้างสคริปต์ด้วยตนเอง",
            "GET /scripts/{id} - ข้อมูลสคริปต์",
            "PUT /scripts/{id} - อัปเดตสคริปต์",
            "DELETE /scripts/{id} - ลบสคริปต์"
        ]
    },
    "mp3_generation": {
        "description": "การสร้างไฟล์เสียงจากสคริปต์",
        "endpoints": [
            "POST /mp3/generate - สร้าง MP3",
            "GET /tts/providers - TTS providers",
            "POST /tts/test - ทดสอบ TTS",
            "GET /tts/emotions/{provider} - อารมณ์ที่รองรับ",
            "DELETE /mp3/{id} - ลบไฟล์ MP3"
        ]
    },
    "personas": {
        "description": "การจัดการ Script และ Voice Personas",
        "endpoints": [
            "GET /personas/script - Script personas",
            "POST /personas/script - สร้าง Script persona",
            "GET /personas/voice - Voice personas", 
            "POST /personas/voice - สร้าง Voice persona",
            "GET /personas/voice/providers/{provider}/voices - เสียงของ provider"
        ]
    },
    "analytics": {
        "description": "การวิเคราะห์และสถิติ",
        "endpoints": [
            "GET /analytics/summary - สรุปการวิเคราะห์",
            "GET /analytics/content-pipeline - สถิติ content pipeline",
            "GET /analytics/efficiency - เมตริกประสิทธิภาพ"
        ]
    },
    "utilities": {
        "description": "ยูทิลิตี้และการทดสอบ",
        "endpoints": [
            "POST /test/ai-generation - ทดสอบ AI generation",
            "GET /export - Export ข้อมูล",
            "GET /system-info - ข้อมูลระบบ",
            "POST /system/cleanup - ทำความสะอาดระบบ",
            "GET /health/detailed - ตรวจสอบสุขภาพแบบละเอียด"
        ]
    }
}

def get_endpoint_summary():
    """
    ดึงสรุปข้อมูล endpoints ทั้งหมด
    """
    return {
        "total_modules": len(ENDPOINT_INFO),
        "modules": ENDPOINT_INFO,
        "api_version": "2.0.0",
        "architecture": "modular"
    }