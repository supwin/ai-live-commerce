# app/api/v1/schemas.py
"""
Pydantic Models สำหรับ Dashboard API
รวม Request/Response schemas ทั้งหมด
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# Product Schemas
class ProductCreateRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    original_price: Optional[float] = None
    discount_percentage: int = Field(default=0, ge=0, le=100)
    category: Optional[str] = None
    brand: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    key_features: List[str] = Field(default_factory=list)
    selling_points: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    use_cases: List[str] = Field(default_factory=list)
    promotion_text: Optional[str] = None
    warranty_info: Optional[str] = None
    shipping_info: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class ProductUpdateRequest(ProductCreateRequest):
    pass

class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    discount_percentage: int
    category: Optional[str]
    brand: Optional[str]
    stock_quantity: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Script Schemas
class AIScriptGenerationRequest(BaseModel):
    product_id: int
    persona_id: int
    mood: str = Field(default="auto")
    count: int = Field(default=3, ge=1, le=10)
    custom_instructions: Optional[str] = None

class ManualScriptCreateRequest(BaseModel):
    product_id: int
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10)
    target_emotion: Optional[str] = None
    call_to_action: Optional[str] = None

class ScriptUpdateRequest(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    target_emotion: Optional[str] = None
    call_to_action: Optional[str] = None

class ScriptResponse(BaseModel):
    id: int
    product_id: int
    title: str
    content: str
    script_type: str
    language: str
    target_emotion: str
    call_to_action: str
    duration_estimate: int
    has_mp3: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# MP3 Generation Schemas
class MP3GenerationRequest(BaseModel):
    script_ids: List[int]
    voice_persona_id: int
    tts_provider: Optional[str] = Field(default="edge")
    quality: str = Field(default="medium", pattern="^(low|medium|high|enhanced)$")
    # เพิ่ม fields ใหม่สำหรับ Enhanced TTS
    emotion: Optional[str] = Field(default="professional")
    intensity: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    volume: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)

class MP3FileResponse(BaseModel):
    id: int
    script_id: int
    filename: str
    file_path: str
    voice_persona_id: int
    tts_provider: str
    duration: float
    file_size: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Persona Schemas
class ScriptPersonaCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)
    speaking_style: Optional[str] = None
    target_audience: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    sample_phrases: List[str] = Field(default_factory=list)
    tone_guidelines: Optional[str] = None
    do_say: List[str] = Field(default_factory=list)
    dont_say: List[str] = Field(default_factory=list)
    default_emotion: str = Field(default="professional")
    available_emotions: List[str] = Field(default_factory=list)

class VoicePersonaCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    tts_provider: str = Field(..., pattern="^(edge|google|elevenlabs)$")
    voice_id: str = Field(..., min_length=1)
    language: str = Field(default="th")
    gender: str = Field(default="female", pattern="^(male|female|neutral)$")
    age_range: Optional[str] = None
    accent: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)
    volume: float = Field(default=1.0, ge=0.5, le=2.0)
    emotion: Optional[str] = None
    emotional_range: List[str] = Field(default_factory=list)
    provider_settings: Dict[str, Any] = Field(default_factory=dict)

class PersonaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Dashboard Stats Schemas
class DashboardStatsResponse(BaseModel):
    products: Dict[str, Any]
    content: Dict[str, Any]
    storage: Dict[str, Any]
    personas: Dict[str, Any]
    recent_activity: Dict[str, Any]
    last_updated: str

# TTS Test Schema
class TTSTestRequest(BaseModel):
    text: str = Field(default="สวัสดีครับ ทดสอบระบบเสียงพูดใหม่")
    provider: str = Field(default="edge")
    emotion: str = Field(default="professional")
    voice_id: Optional[str] = None

class TTSTestResponse(BaseModel):
    success: bool
    message: str
    audio_url: Optional[str]
    file_path: Optional[str]
    provider: str
    emotion: str
    voice_id: str
    text_preview: str
    duration_seconds: float
    contamination_prevented: bool

# Analytics Schemas
class ProductPerformanceResponse(BaseModel):
    product_id: int
    product_name: str
    script_count: int
    mp3_count: int
    completion_rate: float

class ScriptTrendResponse(BaseModel):
    date: str
    scripts_generated: int

class PersonaUsageResponse(BaseModel):
    persona_name: str
    usage_count: int

class AnalyticsSummaryResponse(BaseModel):
    period_days: int
    product_performance: List[ProductPerformanceResponse]
    script_generation_trend: List[ScriptTrendResponse]
    top_personas: List[PersonaUsageResponse]

# Common Response Schemas
class SuccessResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    success: bool = False

class PaginatedResponse(BaseModel):
    total: int
    limit: int
    offset: int
    has_more: bool

class ProductListResponse(PaginatedResponse):
    products: List[ProductResponse]

class ScriptListResponse(BaseModel):
    scripts: List[ScriptResponse]
    total: int = Field(description="จำนวนสคริปต์ทั้งหมด")