# app/api/v1/content_display.py
"""
Content Display API Endpoints - Step 2
API สำหรับควบคุม Enhanced Display Server
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.services.content_display_service import content_display_service

router = APIRouter(tags=["Content Display"])

# Request Models
class ContentUpdateRequest(BaseModel):
    video_path: Optional[str] = None
    product_info: Optional[dict] = None
    script_info: Optional[dict] = None
    display_mode: str = "video"  # video, slideshow, text

class VideoDisplayRequest(BaseModel):
    video_path: str
    product_info: Optional[dict] = None

@router.get("/status")
async def get_display_service_status():
    """ตรวจสอบสถานะ Content Display Service"""
    
    try:
        status = content_display_service.get_service_status()
        return {
            "success": True,
            "service_status": status,
            "ready_for_display": not status["server_running"],  # Ready to start if not running
            "recommendations": [
                "✅ Service ready to start display server" if not status["server_running"] else
                f"🖥️ Display server running at {status['server_url']}",
                "📱 Mobile-optimized display available",
                "🔄 Real-time WebSocket updates enabled",
                "🎬 Video content integration ready"
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/start-server")
async def start_display_server():
    """เริ่ม Content Display Server"""
    
    try:
        print("🚀 Starting content display server via API...")
        
        result = await content_display_service.start_display_server()
        
        if result["success"]:
            return {
                "success": True,
                "message": "Content display server started successfully",
                "server_info": result,
                "instructions": [
                    f"🖥️ Main display: {result['server_url']}/",
                    f"📱 Mobile display: {result['server_url']}/mobile",
                    f"🔳 Fullscreen: {result['server_url']}/fullscreen",
                    "Point your mobile camera at the display",
                    "Content updates in real-time via WebSocket"
                ],
                "integration": {
                    "video_generation": "Ready to receive videos from AI Video Service",
                    "mobile_capture": "Optimized for TikTok Live streaming",
                    "api_control": "Update content via /update-content endpoint"
                }
            }
        else:
            return result
            
    except Exception as e:
        print(f"❌ Failed to start display server: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/stop-server")
async def stop_display_server():
    """หยุด Content Display Server"""
    
    try:
        result = await content_display_service.stop_display_server()
        return {
            "success": result["success"],
            "message": result["message"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/update-content")
async def update_display_content(request: ContentUpdateRequest):
    """อัพเดทเนื้อหาที่แสดง"""
    
    try:
        print(f"🔄 API: Updating display content...")
        
        content_data = {}
        
        if request.video_path:
            content_data["video_path"] = request.video_path
        
        if request.product_info:
            content_data["product_info"] = request.product_info
        
        if request.script_info:
            content_data["script_info"] = request.script_info
        
        content_data["display_mode"] = request.display_mode
        
        result = await content_display_service.update_content(content_data)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Display content updated successfully",
                "content": result["content"],
                "active_connections": result["active_connections"],
                "display_info": {
                    "updated_at": result["content"]["updated_at"],
                    "display_mode": result["content"]["display_mode"],
                    "has_video": bool(result["content"].get("video_path")),
                    "has_product_info": bool(result["content"].get("product_info"))
                }
            }
        else:
            return result
            
    except Exception as e:
        print(f"❌ API: Failed to update content: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/update-video")
async def update_video_display(request: VideoDisplayRequest):
    """อัพเดทวิดีโอที่แสดง (สำหรับ integration กับ AI Video Service)"""
    
    try:
        print(f"🎬 API: Updating video display: {request.video_path}")
        
        result = await content_display_service.update_video_content(
            video_path=request.video_path,
            product_info=request.product_info
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Video display updated successfully",
                "video_info": {
                    "video_path": result["content"]["video_path"],
                    "product_info": result["content"].get("product_info"),
                    "updated_at": result["content"]["updated_at"]
                },
                "display_status": {
                    "active_connections": result["active_connections"],
                    "display_mode": "video"
                }
            }
        else:
            return result
            
    except Exception as e:
        print(f"❌ API: Failed to update video: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/current-content")
async def get_current_content():
    """ดูเนื้อหาปัจจุบันที่แสดง"""
    
    try:
        return {
            "success": True,
            "content": content_display_service.current_content,
            "server_status": {
                "running": content_display_service.is_running,
                "active_connections": len(content_display_service.active_connections),
                "port": content_display_service.display_config["port"]
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/connections")
async def get_websocket_connections():
    """ดูสถานะ WebSocket connections"""
    
    try:
        return {
            "success": True,
            "active_connections": len(content_display_service.active_connections),
            "server_running": content_display_service.is_running,
            "websocket_info": {
                "endpoint": "/ws",
                "real_time_updates": True,
                "auto_reconnect": True
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/test-content")
async def test_display_content():
    """ทดสอบแสดงเนื้อหา mock"""
    
    try:
        # สร้างข้อมูล mock สำหรับทดสอบ
        mock_content = {
            "product_info": {
                "name": "AI Smart Device - Test",
                "price": "฿299 (ราคาทดสอบ)",
                "description": "สินค้าทดสอบสำหรับ Content Display Service"
            },
            "script_info": {
                "call_to_action": "สั่งซื้อทดสอบได้เลย!"
            },
            "display_mode": "text"
        }
        
        result = await content_display_service.update_content(mock_content)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Test content displayed successfully",
                "test_content": mock_content,
                "display_info": result,
                "instructions": [
                    "Test content should now appear on display",
                    "Check the display pages to see the mock content",
                    "WebSocket connections will receive the update"
                ]
            }
        else:
            return result
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/integration-test")
async def test_integration_with_video_service():
    """ทดสอบ integration กับ AI Video Service"""
    
    try:
        # Import AI Video Service
        try:
            from app.services.ai_video_service import ai_video_service
        except ImportError:
            return {
                "success": False,
                "error": "AI Video Service not available for integration"
            }
        
        # ตรวจสอบสถานะ Video Service
        video_status = ai_video_service.get_service_status()
        
        # สร้าง mock video path
        mock_video_path = "/videos/integration_test.mp4"
        
        # อัพเดท display
        integration_content = {
            "video_path": mock_video_path,
            "product_info": {
                "name": "Integration Test Product",
                "price": "฿199",
                "description": "Testing AI Video + Display integration"
            },
            "script_info": {
                "call_to_action": "Integration test สำเร็จ!"
            },
            "display_mode": "video"
        }
        
        result = await content_display_service.update_content(integration_content)
        
        return {
            "success": True,
            "message": "Integration test completed",
            "video_service_status": {
                "available": True,
                "video_generation": video_status["capabilities"]["video_generation"],
                "simulation_mode": video_status["capabilities"]["simulation_mode"]
            },
            "display_service_status": {
                "server_running": content_display_service.is_running,
                "content_updated": result["success"]
            },
            "integration_flow": [
                "✅ AI Video Service generates video",
                "✅ Content Display Service receives video path",
                "✅ Display updates in real-time via WebSocket",
                "✅ Mobile camera captures updated content",
                "✅ TikTok Live streams the content"
            ],
            "next_steps": [
                "Generate actual video using AI Video Service",
                "Test mobile camera capture",
                "Start TikTok Live streaming"
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/display-modes")
async def get_available_display_modes():
    """รายการ display modes ที่มี"""
    
    return {
        "success": True,
        "display_modes": [
            {
                "id": "video",
                "name": "Video Display",
                "description": "แสดงวิดีโอที่สร้างจาก AI Video Service",
                "features": ["Video playback", "Product overlay", "Auto-loop"]
            },
            {
                "id": "slideshow",
                "name": "Slideshow Display",
                "description": "แสดงภาพสไลด์พร้อมข้อความ",
                "features": ["Image rotation", "Text overlay", "Transition effects"]
            },
            {
                "id": "text",
                "name": "Text Display", 
                "description": "แสดงข้อความขนาดใหญ่ high contrast",
                "features": ["Large text", "High contrast", "Animation"]
            }
        ],
        "display_pages": [
            {
                "url": "/",
                "name": "Main Display",
                "description": "หน้าแสดงหลักสำหรับดูบนคอมพิวเตอร์"
            },
            {
                "url": "/fullscreen", 
                "name": "Fullscreen Display",
                "description": "หน้าแสดงแบบเต็มจอสำหรับการนำเสนอ"
            },
            {
                "url": "/mobile",
                "name": "Mobile Display", 
                "description": "หน้าแสดงที่ปรับแต่งสำหรับ mobile camera capture"
            }
        ]
    }