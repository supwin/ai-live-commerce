# app/api/v1/endpoints/scripts.py
"""
Script Management Endpoints
จัดการสคริปต์ AI generation และ manual creation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import os

from ..dependencies import (
    get_db, validate_product_exists, validate_script_exists, validate_persona_exists,
    check_ai_service_availability, ai_script_service,
    Script, ScriptType, ScriptStatus, ScriptPersona, MP3File,
    calculate_duration_estimate, safe_file_delete,
    handle_database_error, handle_service_error
)
from ..schemas import (
    AIScriptGenerationRequest, ManualScriptCreateRequest, ScriptUpdateRequest,
    ScriptResponse, ScriptListResponse, SuccessResponse
)

router = APIRouter()

@router.get("/products/{product_id}/scripts", response_model=ScriptListResponse)
async def get_product_scripts(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    ดึงสคริปต์ทั้งหมดของสินค้า
    
    Returns:
        - รายการสคริปต์เรียงตามวันที่สร้าง
        - จำนวนสคริปต์ทั้งหมด
        - สถานะของแต่ละสคริปต์
    """
    try:
        # ตรวจสอบสินค้าก่อน
        await validate_product_exists(product_id, db)
        
        scripts = db.query(Script).filter(
            Script.product_id == product_id
        ).order_by(desc(Script.created_at)).all()
        
        script_list = []
        for script in scripts:
            script_dict = script.to_dict()
            
            # เพิ่มข้อมูล MP3 count
            mp3_count = db.query(MP3File).filter(MP3File.script_id == script.id).count()
            script_dict['mp3_count'] = mp3_count
            
            script_list.append(script_dict)
        
        return {
            "scripts": script_list,
            "total": len(script_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_product_scripts")

@router.post("/scripts/generate-ai")
async def generate_ai_scripts(
    request: AIScriptGenerationRequest, 
    db: Session = Depends(get_db)
):
    """
    สร้างสคริปต์ด้วย AI - MAIN ENDPOINT พร้อม OpenAI Integration
    
    Features:
    - ใช้ OpenAI API จริง
    - รองรับ personas หลากหลาย
    - ปรับ mood และ emotion ได้
    - สร้างได้หลายสคริปต์พร้อมกัน
    """
    try:
        # ตรวจสอบ dependencies
        product = await validate_product_exists(request.product_id, db)
        persona = await validate_persona_exists(request.persona_id, db, "script")
        ai_service = check_ai_service_availability()
        
        print(f"🎯 AI Script Generation Request:")
        print(f"   Product: {product.name} (ID: {request.product_id})")
        print(f"   Persona: {persona.name} (ID: {request.persona_id})")
        print(f"   Mood: {request.mood}")
        print(f"   Count: {request.count}")
        print(f"   Custom Instructions: {request.custom_instructions}")

        # สร้างสคริปต์ด้วย AI service - เชื่อมต่อ OpenAI จริง
        scripts = await ai_service.generate_scripts(
            db=db,
            product_id=request.product_id,
            persona_id=request.persona_id,
            mood=request.mood,
            count=request.count,
            custom_instructions=request.custom_instructions
        )
        
        print(f"📊 Generated {len(scripts)} AI scripts successfully")
        for i, script in enumerate(scripts):
            print(f"📄 Script {i+1}: {script.get('title', 'No title')[:50]}...")
        
        return {
            "message": f"Generated {len(scripts)} AI scripts successfully",
            "scripts": scripts,
            "product_id": request.product_id,
            "persona_id": request.persona_id,
            "generation_details": {
                "mood": request.mood,
                "count": len(scripts),
                "persona_name": persona.name,
                "product_name": product.name,
                "ai_mode": "openai" if hasattr(ai_service, 'client') and ai_service.client else "simulation",
                "custom_instructions_used": bool(request.custom_instructions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating AI scripts: {e}")
        handle_service_error(e, "AI Script Generation")

@router.post("/scripts/manual", response_model=ScriptResponse)
async def create_manual_script(
    request: ManualScriptCreateRequest, 
    db: Session = Depends(get_db)
):
    """
    สร้างสคริปต์ด้วยตนเอง
    
    Features:
    - ป้อนเนื้อหาเอง
    - คำนวณเวลาอัตโนมัติ
    - ตั้งค่า emotion และ CTA
    """
    try:
        # ตรวจสอบสินค้าก่อน
        product = await validate_product_exists(request.product_id, db)
        
        # คำนวณระยะเวลาโดยประมาณ
        duration_estimate = calculate_duration_estimate(request.content)
        
        # สร้างสคริปต์
        script = Script(
            product_id=request.product_id,
            title=request.title,
            content=request.content,
            script_type=ScriptType.MANUAL,
            language="th",
            target_emotion=request.target_emotion or "professional",
            call_to_action=request.call_to_action or "",
            duration_estimate=duration_estimate,
            status=ScriptStatus.DRAFT
        )
        
        db.add(script)
        db.commit()
        db.refresh(script)
        
        print(f"✅ Created manual script: {script.title}")
        print(f"   📏 Content length: {len(request.content)} chars")
        print(f"   ⏱️ Duration estimate: {duration_estimate}s")
        
        return script.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "create_manual_script")

@router.get("/scripts/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int, 
    db: Session = Depends(get_db)
):
    """
    ดึงข้อมูลสคริปต์ตาม ID พร้อมข้อมูลเพิ่มเติม
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        script_dict = script.to_dict()
        
        # เพิ่มข้อมูล MP3 files
        if hasattr(script, 'mp3_files'):
            mp3_files = [mp3.to_dict() for mp3 in script.mp3_files]
            script_dict['mp3_files'] = mp3_files
            script_dict['mp3_count'] = len(mp3_files)
        
        # เพิ่มข้อมูลสินค้า
        if script.product:
            script_dict['product_name'] = script.product.name
            script_dict['product_sku'] = script.product.sku
        
        return script_dict
        
    except Exception as e:
        handle_database_error(e, "get_script")

@router.put("/scripts/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int, 
    request: ScriptUpdateRequest, 
    db: Session = Depends(get_db)
):
    """
    อัปเดตเนื้อหาสคริปต์ (เฉพาะที่แก้ไขได้)
    
    Restrictions:
    - ไม่สามารถแก้ไขสคริปต์ที่มี MP3 แล้ว
    - ต้องลบ MP3 ก่อนจึงจะแก้ไขได้
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        # ตรวจสอบว่าสคริปต์แก้ไขได้หรือไม่
        if getattr(script, 'has_mp3', False):
            raise HTTPException(
                status_code=400, 
                detail="Script cannot be edited because it has MP3 files. Delete MP3s first to unlock editing."
            )
        
        # อัปเดตฟิลด์
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(script, field, value)
        
        # คำนวณระยะเวลาใหม่หากมีการเปลี่ยน content
        if "content" in update_data:
            script.duration_estimate = calculate_duration_estimate(script.content)
        
        db.commit()
        db.refresh(script)
        
        print(f"✅ Updated script: {script.title}")
        
        return script.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "update_script")

@router.delete("/scripts/{script_id}", response_model=SuccessResponse)
async def delete_script(
    script_id: int, 
    db: Session = Depends(get_db)
):
    """
    ลบสคริปต์และไฟล์ MP3 ที่เกี่ยวข้องทั้งหมด
    
    Features:
    - ลบไฟล์ MP3 จาก disk
    - ลบ records จาก database
    - รายงานจำนวนไฟล์ที่ลบ
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        script_title = script.title
        mp3_count = 0
        
        # ลบไฟล์ MP3 จาก disk
        if hasattr(script, 'mp3_files'):
            for mp3 in script.mp3_files:
                if safe_file_delete(mp3.file_path):
                    print(f"🗑️ Deleted MP3 file: {mp3.file_path}")
                mp3_count += 1
        
        # ลบสคริปต์ (cascade จะลบ MP3 records)
        db.delete(script)
        db.commit()
        
        print(f"🗑️ Deleted script: {script_title}")
        
        return {
            "message": f"Script '{script_title}' deleted successfully",
            "success": True,
            "deleted_mp3_files": mp3_count
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "delete_script")

@router.get("/scripts/{script_id}/mp3")
async def get_script_mp3_files(
    script_id: int, 
    db: Session = Depends(get_db)
):
    """
    ดึงไฟล์ MP3 ทั้งหมดของสคริปต์
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        mp3_files = db.query(MP3File).filter(MP3File.script_id == script_id).all()
        
        return {
            "script_id": script_id,
            "script_title": script.title,
            "mp3_files": [mp3.to_dict() for mp3 in mp3_files],
            "total_files": len(mp3_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "get_script_mp3_files")

@router.delete("/scripts/{script_id}/mp3", response_model=SuccessResponse)
async def delete_script_mp3(
    script_id: int, 
    db: Session = Depends(get_db)
):
    """
    ลบไฟล์ MP3 ทั้งหมดของสคริปต์และปลดล็อกการแก้ไข
    
    Features:
    - ลบ MP3 files ทั้งหมดของสคริปต์
    - ปลดล็อกสคริปต์ให้แก้ไขได้
    - รายงานผลการลบ
    """
    try:
        script = await validate_script_exists(script_id, db)
        
        # ดึง MP3 files ทั้งหมด
        mp3_files = db.query(MP3File).filter(MP3File.script_id == script_id).all()
        
        if not mp3_files:
            raise HTTPException(status_code=404, detail="No MP3 files found for this script")
        
        deleted_files = []
        
        # ลบแต่ละไฟล์
        for mp3_file in mp3_files:
            filename = mp3_file.filename
            
            # ลบไฟล์จาก disk
            if safe_file_delete(mp3_file.file_path):
                print(f"🗑️ Deleted file: {mp3_file.file_path}")
            
            # ลบ record จาก database
            db.delete(mp3_file)
            deleted_files.append(filename)
        
        # ปลดล็อกสคริปต์
        script.has_mp3 = False
        if hasattr(script, 'is_editable'):
            script.is_editable = True
        
        db.commit()
        
        print(f"🔓 Unlocked script for editing: {script.title}")
        
        return {
            "message": f"Deleted {len(deleted_files)} MP3 file(s) for script '{script.title}'",
            "success": True,
            "deleted_files": deleted_files,
            "script_unlocked": True,
            "script_id": script_id
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "delete_script_mp3")

@router.post("/scripts/{script_id}/duplicate", response_model=ScriptResponse)
async def duplicate_script(
    script_id: int,
    new_title: str,
    db: Session = Depends(get_db)
):
    """
    Duplicate สคริปต์พร้อมชื่อใหม่
    """
    try:
        original_script = await validate_script_exists(script_id, db)
        
        # สร้างสคริปต์ใหม่
        script_dict = original_script.to_dict()
        
        # ลบข้อมูลที่ไม่ต้อง copy
        exclude_fields = ['id', 'created_at', 'updated_at', 'has_mp3']
        for field in exclude_fields:
            script_dict.pop(field, None)
        
        # อัปเดตชื่อ
        script_dict['title'] = new_title
        script_dict['has_mp3'] = False
        script_dict['status'] = ScriptStatus.DRAFT
        
        new_script = Script(**script_dict)
        
        db.add(new_script)
        db.commit()
        db.refresh(new_script)
        
        print(f"📋 Duplicated script: {original_script.title} -> {new_script.title}")
        
        return new_script.to_dict()
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        handle_database_error(e, "duplicate_script")

@router.get("/scripts/search")
async def search_scripts(
    query: str,
    product_id: int = None,
    script_type: str = None,
    has_mp3: bool = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    ค้นหาสคริปต์แบบขั้นสูง
    """
    try:
        scripts_query = db.query(Script)
        
        # ค้นหาในชื่อและเนื้อหา
        search_term = f"%{query}%"
        scripts_query = scripts_query.filter(
            (Script.title.ilike(search_term)) |
            (Script.content.ilike(search_term)) |
            (Script.call_to_action.ilike(search_term))
        )
        
        # กรองตามเงื่อนไข
        if product_id:
            scripts_query = scripts_query.filter(Script.product_id == product_id)
            
        if script_type:
            try:
                type_enum = ScriptType(script_type)
                scripts_query = scripts_query.filter(Script.script_type == type_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid script_type: {script_type}")
                
        if has_mp3 is not None:
            scripts_query = scripts_query.filter(Script.has_mp3 == has_mp3)
        
        # จำกัดผลลัพธ์และเรียงลำดับ
        scripts = scripts_query.order_by(desc(Script.created_at)).limit(limit).all()
        
        results = []
        for script in scripts:
            script_dict = script.to_dict()
            if script.product:
                script_dict['product_name'] = script.product.name
            results.append(script_dict)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        handle_database_error(e, "search_scripts")