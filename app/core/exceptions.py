# แก้ไขไฟล์ app/core/exceptions.py ของคุณ
# เพิ่มบรรทัดนี้ที่ด้านบนสุดของไฟล์:

from typing import Optional, Dict


class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

class NotFoundError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AIServiceError(Exception):
    """AI service error"""
    def __init__(self, service: str, message: str, details: Optional[Dict] = None):
        self.service = service
        self.message = message
        self.details = details or {}
        super().__init__(f"AI Service Error ({service}): {message}")
