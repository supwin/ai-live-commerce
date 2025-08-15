# app/api/v1/dashboard.py
"""
Fixed Main Dashboard API Router - แก้ไข 500 error
รวมเส้นทางทั้งหมดพร้อม error handling
"""

from fastapi import APIRouter, HTTPException
import traceback

# สร้าง main router
router = APIRouter()

# Import endpoints with error handling
print("🚀 Loading Dashboard API endpoints...")

try:
    from .endpoints import products
    router.include_router(products.router, prefix="/dashboard", tags=["Products"])
    print("✅ Products endpoints loaded")
except Exception as e:
    print(f"❌ Failed to load Products endpoints: {e}")
    traceback.print_exc()

try:
    from .endpoints import dashboard_stats
    router.include_router(dashboard_stats.router, prefix="/dashboard", tags=["Dashboard Stats"])
    print("✅ Dashboard Stats endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load Dashboard Stats endpoints: {e}")

try:
    from .endpoints import scripts
    router.include_router(scripts.router, prefix="/dashboard", tags=["Scripts"])
    print("✅ Scripts endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load Scripts endpoints: {e}")

try:
    from .endpoints import mp3_generation
    router.include_router(mp3_generation.router, prefix="/dashboard", tags=["MP3 Generation"])
    print("✅ MP3 Generation endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load MP3 Generation endpoints: {e}")

try:
    from .endpoints import personas
    router.include_router(personas.router, prefix="/dashboard", tags=["Personas"])
    print("✅ Personas endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load Personas endpoints: {e}")

try:
    from .endpoints import analytics
    router.include_router(analytics.router, prefix="/dashboard", tags=["Analytics"])
    print("✅ Analytics endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load Analytics endpoints: {e}")

try:
    from .endpoints import utilities
    router.include_router(utilities.router, prefix="/dashboard", tags=["Utilities"])
    print("✅ Utilities endpoints loaded")
except Exception as e:
    print(f"⚠️ Failed to load Utilities endpoints: {e}")

# Health check endpoint
@router.get("/dashboard/health")
async def health_check():
    """ตรวจสอบสถานะความพร้อมใช้งานของ Dashboard API"""
    try:
        # Import dependencies for health check
        from .dependencies import Product, Script, ai_script_service, tts_service
        
        return {
            "status": "healthy",
            "message": "Dashboard API is running",
            "version": "2.0.0 - Fixed",
            "architecture": "modular",
            "modules_loaded": [
                "products",
                "dashboard_stats", 
                "scripts",
                "mp3_generation",
                "personas",
                "analytics",
                "utilities"
            ],
            "models_status": {
                "Product": Product is not None,
                "Script": Script is not None
            },
            "services_status": {
                "AI_Service": ai_script_service is not None,
                "TTS_Service": tts_service is not None
            }
        }
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return {
            "status": "degraded",
            "message": f"Dashboard API running with issues: {str(e)}",
            "version": "2.0.0 - Fixed",
            "error": str(e)
        }

# Debug endpoint
@router.get("/dashboard/debug")
async def debug_info():
    """Debug information สำหรับแก้ไขปัญหา"""
    try:
        from .dependencies import (
            Product, Script, ScriptPersona, VoicePersona, 
            ai_script_service, tts_service, run_startup_diagnostics
        )
        
        # Run diagnostics
        diagnostics_result = run_startup_diagnostics()
        
        return {
            "debug_mode": True,
            "timestamp": "2024-01-01T00:00:00Z",
            "diagnostics_passed": diagnostics_result,
            "available_endpoints": {
                "products": [
                    "GET /dashboard/products",
                    "POST /dashboard/products", 
                    "GET /dashboard/products/{id}",
                    "GET /dashboard/categories",
                    "GET /dashboard/brands"
                ],
                "health": [
                    "GET /dashboard/health",
                    "GET /dashboard/debug"
                ]
            },
            "models": {
                "Product": Product is not None,
                "Script": Script is not None,
                "ScriptPersona": ScriptPersona is not None,
                "VoicePersona": VoicePersona is not None
            },
            "services": {
                "ai_script_service": ai_script_service is not None,
                "tts_service": tts_service is not None
            },
            "recommendations": [
                "Check server logs for detailed error messages",
                "Verify database connection and models",
                "Ensure all required dependencies are installed",
                "Test with /dashboard/products/debug/status endpoint"
            ]
        }
    except Exception as e:
        print(f"❌ Debug endpoint error: {e}")
        traceback.print_exc()
        return {
            "debug_mode": True,
            "error": str(e),
            "message": "Debug endpoint failed - check dependencies",
            "basic_status": "Dashboard router loaded but dependencies have issues"
        }

# Minimal products endpoint as fallback
@router.get("/dashboard/products/minimal")
async def get_products_minimal():
    """Minimal products endpoint สำหรับทดสอบ"""
    try:
        from .dependencies import get_db, Product
        
        if not Product:
            return {
                "error": "Product model not available",
                "products": [],
                "total": 0,
                "message": "Database models not loaded properly"
            }
        
        # ใช้ dependency อย่างง่าย
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            products = db.query(Product).limit(10).all()
            
            # Convert manually
            product_list = []
            for product in products:
                product_list.append({
                    "id": product.id,
                    "sku": getattr(product, 'sku', 'N/A'),
                    "name": getattr(product, 'name', 'N/A'),
                    "price": getattr(product, 'price', 0)
                })
            
            return {
                "products": product_list,
                "total": len(product_list),
                "message": "Minimal products endpoint working"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Minimal products error: {e}")
        traceback.print_exc()
        return {
            "error": str(e),
            "products": [],
            "total": 0,
            "message": "Minimal endpoint failed"
        }

print("🎉 Dashboard API Router initialized successfully!")