# app/api/v1/endpoints/products.py
"""
Fixed Product Management Endpoints
แก้ไขปัญหา 500 error และเพิ่ม error handling
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from typing import List, Optional
import os
import traceback

from ..dependencies import (
    get_db, validate_product_exists, check_models_availability,
    Product, ProductStatus, Script, MP3File, Video,
    handle_database_error, safe_file_delete
)

router = APIRouter()

# ตรวจสอบก่อนที่จะรัน endpoints
@router.on_event("startup")
async def startup_check():
    """ตรวจสอบ dependencies เมื่อเริ่มต้น"""
    try:
        check_models_availability()
        print("✅ Products endpoints ready")
    except Exception as e:
        print(f"❌ Products endpoints not ready: {e}")

@router.get("/products")
async def get_products(
    category: Optional[str] = Query(None, description="กรองตามหมวดหมู่"),
    status: Optional[str] = Query(None, description="กรองตามสถานะ"),
    search: Optional[str] = Query(None, description="ค้นหาจากชื่อ, SKU, รายละเอียด, หรือแบรนด์"),
    has_scripts: Optional[bool] = Query(None, description="กรองสินค้าที่มีสคริปต์"),
    has_mp3s: Optional[bool] = Query(None, description="กรองสินค้าที่มี MP3"),
    limit: int = Query(50, ge=1, le=100, description="จำนวนสินค้าต่อหน้า"),
    offset: int = Query(0, ge=0, description="เลื่อนหน้า"),
    db: Session = Depends(get_db)
):
    """
    ดึงรายการสินค้าพร้อมการกรองและแบ่งหน้า - Fixed Version
    """
    try:
        print("🔍 DEBUG: Starting get_products API call") 
        
        # ตรวจสอบ models ก่อน
        if not Product:
            raise HTTPException(
                status_code=500, 
                detail="Product model not available. Please check database configuration."
            )
        
        print("🔍 DEBUG: Product model available, creating query")
        query = db.query(Product)
        print("🔍 DEBUG: Initial query created successfully") 
        
        # Apply filters with error handling
        try:
            if category and category.strip():
                query = query.filter(Product.category == category.strip())
                print(f"🔍 DEBUG: Applied category filter: {category}")
                
            if status and status.strip():
                try:
                    if ProductStatus:
                        status_enum = ProductStatus(status.strip())
                        query = query.filter(Product.status == status_enum)
                        print(f"🔍 DEBUG: Applied status filter: {status}")
                    else:
                        print("⚠️ ProductStatus enum not available, skipping status filter")
                except ValueError as e:
                    print(f"❌ Invalid status value: {status}")
                    raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
                
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    (Product.name.ilike(search_term)) |
                    (Product.sku.ilike(search_term)) |
                    (Product.description.ilike(search_term)) |
                    (Product.brand.ilike(search_term))
                )
                print(f"🔍 DEBUG: Applied search filter: {search}")
                
            if has_scripts is not None:
                if Script:
                    if has_scripts:
                        query = query.filter(Product.scripts.any())
                    else:
                        query = query.filter(~Product.scripts.any())
                    print(f"🔍 DEBUG: Applied has_scripts filter: {has_scripts}")
                else:
                    print("⚠️ Script model not available, skipping has_scripts filter")
                    
            if has_mp3s is not None:
                if Script and MP3File:
                    if has_mp3s:
                        query = query.filter(Product.scripts.any(Script.has_mp3 == True))
                    else:
                        query = query.filter(~Product.scripts.any(Script.has_mp3 == True))
                    print(f"🔍 DEBUG: Applied has_mp3s filter: {has_mp3s}")
                else:
                    print("⚠️ Script/MP3File models not available, skipping has_mp3s filter")
        
        except Exception as filter_error:
            print(f"❌ Error applying filters: {filter_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=400, 
                detail=f"Error applying filters: {str(filter_error)}"
            )
        
        # Get total count
        try:
            print("🔍 DEBUG: Getting total count")
            total = query.count()
            print(f"🔍 DEBUG: Total products found: {total}")
        except Exception as count_error:
            print(f"❌ Error getting count: {count_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Error counting products"
            )
        
        # Apply pagination and ordering
        try:
            print("🔍 DEBUG: Applying pagination and ordering")
            products = query.order_by(desc(Product.created_at)).offset(offset).limit(limit).all()
            print(f"🔍 DEBUG: Retrieved {len(products)} products")
        except Exception as query_error:
            print(f"❌ Error executing query: {query_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Error retrieving products"
            )
        
        # Convert to dict safely
        try:
            print("🔍 DEBUG: Converting products to dict")
            product_list = []
            for i, product in enumerate(products):
                try:
                    if hasattr(product, 'to_dict'):
                        product_dict = product.to_dict()
                    else:
                        # Manual conversion if to_dict not available
                        product_dict = {
                            'id': product.id,
                            'sku': product.sku,
                            'name': product.name,
                            'description': getattr(product, 'description', None),
                            'price': product.price,
                            'status': product.status.value if hasattr(product.status, 'value') else str(product.status),
                            'created_at': product.created_at.isoformat() if hasattr(product.created_at, 'isoformat') else str(product.created_at),
                            'updated_at': getattr(product, 'updated_at', None)
                        }
                    product_list.append(product_dict)
                    
                except Exception as convert_error:
                    print(f"❌ Error converting product {i}: {convert_error}")
                    # Continue with other products
                    continue
            
            print(f"✅ Successfully converted {len(product_list)} products")
            
        except Exception as conversion_error:
            print(f"❌ Error in product conversion: {conversion_error}")
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail="Error processing products data"
            )
        
        # Return response
        response = {
            "products": product_list,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
        
        print(f"✅ Successfully returning {len(product_list)} products")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Unexpected error in get_products: {e}")
        traceback.print_exc()
        handle_database_error(e, "get_products")

@router.post("/products")
async def create_product(
    product_data: dict,  # รับเป็น dict แทน Pydantic model ชั่วคราว
    db: Session = Depends(get_db)
):
    """
    สร้างสินค้าใหม่ - Simplified version
    """
    try:
        print(f"📝 Creating product with data: {product_data}")
        
        # ตรวจสอบ models
        if not Product:
            raise HTTPException(status_code=500, detail="Product model not available")
        
        # ตรวจสอบข้อมูลพื้นฐาน
        required_fields = ['sku', 'name', 'price']
        for field in required_fields:
            if field not in product_data:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # ตรวจสอบ SKU ซ้ำ
        existing = db.query(Product).filter(Product.sku == product_data['sku']).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"SKU '{product_data['sku']}' already exists")
        
        # สร้าง product
        product_fields = {
            'sku': product_data['sku'],
            'name': product_data['name'],
            'price': float(product_data['price']),
            'description': product_data.get('description'),
            'category': product_data.get('category'),
            'brand': product_data.get('brand'),
            'stock_quantity': product_data.get('stock_quantity', 0)
        }
        
        # Set status
        if ProductStatus:
            product_fields['status'] = ProductStatus.ACTIVE
        
        product = Product(**product_fields)
        
        db.add(product)
        db.commit()
        db.refresh(product)
        
        print(f"✅ Created product: {product.name} (SKU: {product.sku})")
        
        # Return response
        if hasattr(product, 'to_dict'):
            return product.to_dict()
        else:
            return {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'price': product.price,
                'message': 'Product created successfully'
            }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating product: {e}")
        traceback.print_exc()
        handle_database_error(e, "create_product")

@router.get("/products/{product_id}")
async def get_product(
    product_id: int, 
    db: Session = Depends(get_db)
):
    """
    ดึงข้อมูลสินค้าตาม ID
    """
    try:
        if not Product:
            raise HTTPException(status_code=500, detail="Product model not available")
            
        product = await validate_product_exists(product_id, db)
        
        # สร้าง response
        if hasattr(product, 'to_dict'):
            product_dict = product.to_dict()
        else:
            product_dict = {
                'id': product.id,
                'sku': product.sku,
                'name': product.name,
                'price': product.price,
                'description': getattr(product, 'description', None),
                'status': product.status.value if hasattr(product.status, 'value') else str(product.status)
            }
        
        # เพิ่มข้อมูลเพิ่มเติมถ้า models พร้อม
        if Script:
            scripts_count = db.query(Script).filter(Script.product_id == product_id).count()
            product_dict['scripts_count'] = scripts_count
            
            if MP3File:
                mp3s_count = db.query(MP3File).join(Script).filter(Script.product_id == product_id).count()
                product_dict['mp3s_count'] = mp3s_count
                product_dict['content_ready'] = scripts_count > 0 and mp3s_count > 0
        
        return product_dict
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting product: {e}")
        handle_database_error(e, "get_product")

@router.get("/categories")
async def get_categories(db: Session = Depends(get_db)):
    """
    ดึงรายการหมวดหมู่สินค้าที่มีอยู่
    """
    try:
        if not Product:
            return {"categories": [], "total": 0, "message": "Product model not available"}
        
        categories = db.query(Product.category).filter(
            Product.category.isnot(None),
            Product.category != ""
        ).distinct().all()
        
        category_list = [cat.category for cat in categories if cat.category]
        category_list.sort()
        
        return {
            "categories": category_list,
            "total": len(category_list)
        }
        
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        return {"categories": [], "total": 0, "error": str(e)}

@router.get("/brands")
async def get_brands(db: Session = Depends(get_db)):
    """
    ดึงรายการแบรนด์สินค้าที่มีอยู่
    """
    try:
        if not Product:
            return {"brands": [], "total": 0, "message": "Product model not available"}
        
        brands = db.query(Product.brand).filter(
            Product.brand.isnot(None),
            Product.brand != ""
        ).distinct().all()
        
        brand_list = [brand.brand for brand in brands if brand.brand]
        brand_list.sort()
        
        return {
            "brands": brand_list,
            "total": len(brand_list)
        }
        
    except Exception as e:
        print(f"❌ Error getting brands: {e}")
        return {"brands": [], "total": 0, "error": str(e)}

# Diagnostic endpoint
@router.get("/products/debug/status")
async def get_products_debug_status():
    """
    ตรวจสอบสถานะของ Products endpoint สำหรับ debugging
    """
    return {
        "products_endpoint_status": "active",
        "models_available": {
            "Product": Product is not None,
            "ProductStatus": ProductStatus is not None,
            "Script": Script is not None,
            "MP3File": MP3File is not None
        },
        "endpoints": [
            "GET /products - List products with filtering",
            "POST /products - Create new product", 
            "GET /products/{id} - Get product details",
            "GET /categories - Get product categories",
            "GET /brands - Get product brands"
        ],
        "debug_info": {
            "module": "products.py",
            "version": "fixed_2.0.0",
            "error_handling": "enhanced"
        }
    }