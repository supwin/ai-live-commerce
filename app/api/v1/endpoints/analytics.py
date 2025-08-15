# app/api/v1/endpoints/analytics.py
"""
Analytics Endpoints
จัดการข้อมูลสถิติและการวิเคราะห์
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from typing import Optional

from ..dependencies import (
    get_db, get_date_range,
    Product, Script, ScriptType, MP3File, ScriptPersona, VoicePersona,
    handle_database_error
)
from ..schemas import AnalyticsSummaryResponse

router = APIRouter()

@router.get("/analytics/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    days: int = Query(30, ge=1, le=365, description="จำนวนวันย้อนหลัง"),
    db: Session = Depends(get_db)
):
    """
    ดึงสรุปการวิเคราะห์สำหรับ dashboard
    
    Features:
    - ประสิทธิภาพสินค้า
    - แนวโน้มการสร้างสคริปต์
    - การใช้งาน personas
    - อัตราความสำเร็จ
    """
    try:
        cutoff_date = get_date_range(days)
        
        # Product performance
        product_stats = db.query(
            Product.id,
            Product.name,
            func.count(Script.id).label('script_count'),
            func.count(MP3File.id).label('mp3_count')
        ).outerjoin(Script).outerjoin(MP3File).group_by(Product.id, Product.name).all()
        
        # Script generation trends
        script_trends = db.query(
            func.date(Script.created_at).label('date'),
            func.count(Script.id).label('count')
        ).filter(Script.created_at >= cutoff_date).group_by(func.date(Script.created_at)).all()
        
        # Persona usage
        persona_usage = db.query(
            ScriptPersona.name,
            func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0).label('usage_count')
        ).filter(
            func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0) > 0
        ).order_by(desc(func.coalesce(getattr(ScriptPersona, 'usage_count', 0), 0))).limit(10).all()
        
        return {
            "period_days": days,
            "product_performance": [
                {
                    "product_id": stat.id,
                    "product_name": stat.name,
                    "script_count": stat.script_count or 0,
                    "mp3_count": stat.mp3_count or 0,
                    "completion_rate": round((stat.mp3_count / max(stat.script_count, 1)) * 100, 1) if stat.script_count else 0
                }
                for stat in product_stats
            ],
            "script_generation_trend": [
                {
                    "date": trend.date.isoformat() if hasattr(trend.date, 'isoformat') else str(trend.date),
                    "scripts_generated": trend.count
                }
                for trend in script_trends
            ],
            "top_personas": [
                {
                    "persona_name": usage.name,
                    "usage_count": usage.usage_count
                }
                for usage in persona_usage
            ]
        }
        
    except Exception as e:
        handle_database_error(e, "get_analytics_summary")

@router.get("/analytics/content-pipeline")
async def get_content_pipeline_stats(
    days: int = Query(7, ge=1, le=90, description="จำนวนวันย้อนหลัง"),
    db: Session = Depends(get_db)
):
    """
    ดึงสถิติ content pipeline (สินค้า -> สคริปต์ -> MP3)
    """
    try:
        cutoff_date = get_date_range(days)
        
        # Pipeline stages
        total_products = db.query(Product).count()
        products_with_scripts = db.query(Product).filter(Product.scripts.any()).count()
        products_with_mp3s = db.query(Product).filter(
            Product.scripts.any(Script.has_mp3 == True)
        ).count()
        
        # Recent activity
        new_scripts = db.query(Script).filter(Script.created_at >= cutoff_date).count()
        new_mp3s = db.query(MP3File).filter(MP3File.created_at >= cutoff_date).count()
        
        # Conversion rates
        script_conversion = round((products_with_scripts / max(total_products, 1)) * 100, 1)
        mp3_conversion = round((products_with_mp3s / max(products_with_scripts, 1)) * 100, 1)
        full_pipeline = round((products_with_mp3s / max(total_products, 1)) * 100, 1)
        
        return {
            "period_days": days,
            "pipeline_stages": {
                "total_products": total_products,
                "products_with_scripts": products_with_scripts,
                "products_with_mp3s": products_with_mp3s,
                "fully_ready": products_with_mp3s
            },
            "conversion_rates": {
                "product_to_script": script_conversion,
                "script_to_mp3": mp3_conversion,
                "full_pipeline": full_pipeline
            },
            "recent_activity": {
                "new_scripts": new_scripts,
                "new_mp3s": new_mp3s,
                "daily_script_average": round(new_scripts / days, 1),
                "daily_mp3_average": round(new_mp3s / days, 1)
            },
            "recommendations": [
                f"เพิ่มสคริปต์สำหรับสินค้า {total_products - products_with_scripts} รายการ",
                f"สร้าง MP3 สำหรับสคริปต์ {products_with_scripts - products_with_mp3s} รายการ"
            ] if total_products > products_with_mp3s else ["Content pipeline พร้อมใช้งานแล้ว!"]
        }
        
    except Exception as e:
        handle_database_error(e, "get_content_pipeline_stats")

@router.get("/analytics/efficiency")
async def get_efficiency_metrics(
    days: int = Query(30, ge=1, le=365, description="จำนวนวันย้อนหลัง"),
    db: Session = Depends(get_db)
):
    """
    ดึงเมตริกประสิทธิภาพของระบบ
    """
    try:
        cutoff_date = get_date_range(days)
        
        # AI vs Manual script creation
        total_scripts = db.query(Script).filter(Script.created_at >= cutoff_date).count()
        ai_scripts = db.query(Script).filter(
            Script.created_at >= cutoff_date,
            Script.script_type == ScriptType.AI_GENERATED
        ).count()
        manual_scripts = total_scripts - ai_scripts
        
        # MP3 generation success rate
        total_mp3_attempts = db.query(MP3File).filter(MP3File.created_at >= cutoff_date).count()
        successful_mp3s = db.query(MP3File).filter(
            MP3File.created_at >= cutoff_date,
            MP3File.status == "completed"
        ).count()
        failed_mp3s = total_mp3_attempts - successful_mp3s
        
        # Average processing time (mock data)
        avg_script_time = 45  # seconds
        avg_mp3_time = 15   # seconds per script
        
        return {
            "period_days": days,
            "script_efficiency": {
                "total_scripts": total_scripts,
                "ai_generated": ai_scripts,
                "manual_created": manual_scripts,
                "ai_adoption_rate": round((ai_scripts / max(total_scripts, 1)) * 100, 1),
                "avg_generation_time": avg_script_time
            },
            "mp3_efficiency": {
                "total_attempts": total_mp3_attempts,
                "successful": successful_mp3s,
                "failed": failed_mp3s,
                "success_rate": round((successful_mp3s / max(total_mp3_attempts, 1)) * 100, 1),
                "avg_generation_time": avg_mp3_time
            },
            "overall_metrics": {
                "automation_level": round((ai_scripts / max(total_scripts, 1)) * 100, 1),
                "content_throughput": total_scripts + successful_mp3s,
                "quality_score": round((successful_mp3s / max(total_mp3_attempts, 1)) * 100, 1)
            }
        }
        
    except Exception as e:
        handle_database_error(e, "get_efficiency_metrics")

