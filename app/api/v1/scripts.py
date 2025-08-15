# app/api/v1/endpoints/scripts.py
"""
Fixed Script Management Endpoints - แก้ไข response format
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import os
import traceback

from ..dependencies import (
    get_db, validate_product_exists, validate_script_exists, validate_persona_exists,
    check_ai_service_availability, ai_script_service,
    Script, ScriptType, ScriptStatus, ScriptPersona, MP3File,
    calculate_duration_estimate, safe_file_delete,
    handle_database_error, handle_service_error
)

router = APIRouter()

@router.get("/products/{product_id}/scripts")
async def get_product_scripts(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    ดึงสคริปต์ทั้งหมดของสินค้า - Fixed Response Format
    
    Returns:
        - scripts: Array of script objects  
        - total: จำนวนสคริปต์ทั้งหมด
    """
    try:
        print(f"🔍 Loading scripts for product {product_id}")
        
        # ตรวจสอบว่า models พร้อม
        if not Script:
            print("❌ Script model not available")
            return {
                "scripts": [],
                "total": 0,
                "error": "Script model not available"
            }
        
        # ตรวจสอบสินค้าก่อน
        try:
            await validate_product_exists(product_id, db)
            print(f"✅ Product {product_id} exists")
        except HTTPException as e:
            print(f"❌ Product validation failed: {e.detail}")
            return {
                "scripts": [],
                "total": 0,
                "error": f"Product not found: {e.detail}"
            }
        
        # ดึงสคริปต์
        try:
            scripts = db.query(Script).filter(
                Script.product_id == product_id
            ).order_by(desc(Script.created_at)).all()
            
            print(f"📊 Found {len(scripts)} scripts for product {product_id}")
            
        except Exception as query_error:
            print(f"❌ Database query error: {query_error}")
            traceback.print_exc()
            return {
                "scripts": [],
                "total": 0,
                "error": f"Database query failed: {str(query_error)}"
            }
        
        # แปลงข้อมูลอย่างปลอดภัย
        script_list = []
        for i, script in enumerate(scripts):
            try:
                # สร้าง script dict แบบ manual เพื่อความปลอดภัย
                script_dict = {
                    "id": getattr(script, 'id', None),
                    "product_id": getattr(script, 'product_id', product_id),
                    "title": getattr(script, 'title', f"Script {i+1}"),
                    "content": getattr(script, 'content', ''),
                    "script_type": getattr(script, 'script_type', 'manual'),
                    "language": getattr(script, 'language', 'th'),
                    "target_emotion": getattr(script, 'target_emotion', 'professional'),
                    "call_to_action": getattr(script, 'call_to_action', ''),
                    "duration_estimate": getattr(script, 'duration_estimate', 60),
                    "has_mp3": getattr(script, 'has_mp3', False),
                    "status": getattr(script, 'status', 'draft'),
                    "created_at": script.created_at.isoformat() if hasattr(script, 'created_at') and script.created_at else None
                }
                
                # เพิ่มข้อมูล MP3 count ถ้า MP3File model พร้อม
                if MP3File:
                    try:
                        mp3_count = db.query(MP3File).filter(MP3File.script_id == script.id).count()
                        script_dict['mp3_count'] = mp3_count
                    except Exception as mp3_error:
                        print(f"⚠️ Error counting MP3s for script {script.id}: {mp3_error}")
                        script_dict['mp3_count'] = 0
                else:
                    script_dict['mp3_count'] = 0
                
                # แปลง enum values เป็น string
                if hasattr(script_dict['script_type'], 'value'):
                    script_dict['script_type'] = script_dict['script_type'].value
                if hasattr(script_dict['status'], 'value'):
                    script_dict['status'] = script_dict['status'].value
                
                script_list.append(script_dict)
                
            except Exception as conversion_error:
                print(f"❌ Error converting script {i}: {conversion_error}")
                # เพิ่ม fallback script
                script_list.append({
                    "id": getattr(script, 'id', i),
                    "product_id": product_id,
                    "title": f"Script {i+1} (Error)",
                    "content": "Error loading script content",
                    "script_type": "unknown",
                    "language": "th",
                    "target_emotion": "professional",
                    "call_to_action": "",
                    "duration_estimate": 60,
                    "has_mp3": False,
                    "status": "error",
                    "mp3_count": 0,
                    "created_at": None,
                    "error": f"Conversion error: {str(conversion_error)}"
                })
                continue
        
        # สร้าง response ที่มั่นใจว่าเป็น array
        response = {
            "scripts": script_list,  # 🔧 มั่นใจว่าเป็น array เสมอ
            "total": len(script_list),
            "product_id": product_id
        }
        
        print(f"✅ Successfully returning {len(script_list)} scripts")
        print(f"📋 Response type: scripts={type(script_list)}, total={type(len(script_list))}")
        
        return response
        
    except Exception as e:
        print(f"❌ Unexpected error in get_product_scripts: {e}")
        traceback.print_exc()
        
        # Return safe fallback response
        return {
            "scripts": [],  # 🔧 เสมอเป็น empty array
            "total": 0,
            "product_id": product_id,
            "error": f"Unexpected error: {str(e)}"
        }

@router.post("/scripts/generate-ai")
async def generate_ai_scripts(
    request: dict,  # รับเป็น dict แทน Pydantic model ชั่วคราว
    db: Session = Depends(get_db)
):
    """
    สร้างสคริปต์ด้วย AI - Fixed Version
    """
    try:
        print(f"🎯 AI Script Generation Request: {request}")
        
        # ตรวจสอบข้อมูลพื้นฐาน
        required_fields = ['product_id', 'persona_id']
        for field in required_fields:
            if field not in request:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        product_id = request['product_id']
        persona_id = request['persona_id']
        mood = request.get('mood', 'auto')
        count = request.get('count', 3)
        custom_instructions = request.get('custom_instructions')
        
        # ตรวจสอบ dependencies
        product = await validate_product_exists(product_id, db)
        persona = await validate_persona_exists(persona_id, db, "script")
        ai_service = check_ai_service_availability()
        
        print(f"   Product: {product.name} (ID: {product_id})")
        print(f"   Persona: {persona.name} (ID: {persona_id})")
        print(f"   Mood: {mood}, Count: {count}")

        # สร้างสคริปต์ด้วย AI service
        scripts = await ai_service.generate_scripts(
            db=db,
            product_id=product_id,
            persona_id=persona_id,
            mood=mood,
            count=count,
            custom_instructions=custom_instructions
        )
        
        print(f"📊 Generated {len(scripts)} AI scripts successfully")
        
        # มั่นใจว่า scripts เป็น array
        if not isinstance(scripts, list):
            scripts = [scripts] if scripts else []
        
        return {
            "message": f"Generated {len(scripts)} AI scripts successfully",
            "scripts": scripts,  # 🔧 มั่นใจว่าเป็น array
            "product_id": product_id,
            "persona_id": persona_id,
            "generation_details": {
                "mood": mood,
                "count": len(scripts),
                "persona_name": persona.name,
                "product_name": product.name,
                "ai_mode": "openai" if hasattr(ai_service, 'client') and ai_service.client else "simulation",
                "custom_instructions_used": bool(custom_instructions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating AI scripts: {e}")
        traceback.print_exc()
        handle_service_error(e, "AI Script Generation")

@router.get("/scripts/debug/test-response")
async def test_scripts_response():
    """
    ทดสอบ response format สำหรับ debugging
    """
    mock_scripts = [
        {
            "id": 1,
            "product_id": 1,
            "title": "Test Script 1",
            "content": "This is test script content",
            "script_type": "manual",
            "language": "th",
            "target_emotion": "professional",
            "call_to_action": "Buy now!",
            "duration_estimate": 60,
            "has_mp3": False,
            "status": "draft",
            "mp3_count": 0,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": 2,
            "product_id": 1,
            "title": "Test Script 2",
            "content": "This is another test script",
            "script_type": "ai_generated",
            "language": "th",
            "target_emotion": "excited",
            "call_to_action": "Order today!",
            "duration_estimate": 45,
            "has_mp3": True,
            "status": "completed",
            "mp3_count": 2,
            "created_at": "2024-01-01T01:00:00Z"
        }
    ]
    
    return {
        "scripts": mock_scripts,
        "total": len(mock_scripts),
        "product_id": 1,
        "message": "Test response - scripts is always an array",
        "debug_info": {
            "scripts_type": str(type(mock_scripts)),
            "scripts_length": len(mock_scripts),
            "is_array": isinstance(mock_scripts, list)
        }
    }

@router.get("/scripts/debug/product/{product_id}")
async def debug_product_scripts(product_id: int, db: Session = Depends(get_db)):
    """
    Debug endpoint สำหรับ scripts ของสินค้าเฉพาะ
    """
    try:
        # Raw database query
        if Script:
            scripts = db.query(Script).filter(Script.product_id == product_id).all()
            script_data = []
            
            for script in scripts:
                script_data.append({
                    "id": script.id,
                    "title": getattr(script, 'title', 'No title'),
                    "type": str(type(script)),
                    "attributes": [attr for attr in dir(script) if not attr.startswith('_')]
                })
        else:
            script_data = []
        
        return {
            "product_id": product_id,
            "script_model_available": Script is not None,
            "raw_scripts_count": len(script_data),
            "scripts_sample": script_data[:3],  # First 3 for debugging
            "debug_timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        return {
            "product_id": product_id,
            "error": str(e),
            "script_model_available": Script is not None
        }