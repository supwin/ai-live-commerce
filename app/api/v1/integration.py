# app/api/v1/integration.py
"""
Integration API - Control the entire AI Live Commerce system
Fixed router prefix and error handling
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Import with error handling
try:
    from app.services.integration_hub import live_orchestrator
    print("✅ Integration hub imported")
except ImportError as e:
    print(f"❌ Integration hub import failed: {e}")
    live_orchestrator = None

# Optional database import
try:
    from app.core.database import get_db
    from app.models.product import Product
    from sqlalchemy.orm import Session
    database_available = True
except ImportError as e:
    print(f"⚠️ Database imports failed: {e}")
    database_available = False
    get_db = None
    Product = None
    Session = None

# FIXED: Use only /api/integration prefix (remove double prefix)
router = APIRouter(prefix="/api/integration", tags=["integration"])

# Request models
class StartSessionRequest(BaseModel):
    platform: str = "facebook"
    product_focus: Optional[str] = None

class PresentProductRequest(BaseModel):
    product_id: str
    use_saved_script: bool = True

class AutoResponseRequest(BaseModel):
    enabled: bool

class CustomMessageRequest(BaseModel):
    message: str
    platform: Optional[str] = None

# Session control endpoints
@router.post("/session/start")
async def start_live_session(request: StartSessionRequest):
    """Start integrated AI live commerce session"""
    try:
        if not live_orchestrator:
            return {
                "success": False,
                "message": "Integration hub not available - Mock Mode",
                "status": {
                    "active": True,
                    "platform": request.platform,
                    "mock_mode": True
                }
            }
        
        print(f"🚀 Starting session request: platform={request.platform}")
        
        success = await live_orchestrator.start_live_session(
            platform=request.platform,
            product_focus=request.product_focus
        )
        
        if success:
            return {
                "success": True,
                "message": f"Live commerce session started on {request.platform}",
                "status": live_orchestrator.get_session_status()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to start session")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Session start error: {e}")
        import traceback
        traceback.print_exc()
        
        # Return graceful error instead of raising
        return {
            "success": False,
            "message": f"Session start failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

@router.post("/session/stop")
async def stop_live_session():
    """Stop live commerce session"""
    try:
        if not live_orchestrator:
            return {
                "success": True,
                "message": "Live commerce session stopped (Mock Mode)",
                "final_stats": {"mock_mode": True}
            }
        
        await live_orchestrator.stop_live_session()
        
        return {
            "success": True,
            "message": "Live commerce session stopped",
            "final_stats": live_orchestrator.get_session_status()
        }
        
    except Exception as e:
        print(f"❌ Session stop error: {e}")
        return {
            "success": False,
            "message": f"Session stop failed: {str(e)}",
            "error": str(e)
        }

@router.get("/session/status")
async def get_session_status():
    """Get current session status"""
    try:
        if not live_orchestrator:
            return {
                "active": False,
                "platform": None,
                "error": "Integration hub not available",
                "mock_mode": True
            }
        
        return live_orchestrator.get_session_status()
        
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return {
            "active": False,
            "error": str(e),
            "mock_mode": True
        }

# Product presentation endpoints
@router.post("/present-product")
async def present_product(request: PresentProductRequest, db: Session = Depends(get_db) if database_available else None):
    """Present a product using AI + Avatar"""
    try:
        if not live_orchestrator:
            # Mock response
            return {
                "success": True,
                "message": f"Mock: Presenting product {request.product_id}",
                "product": {
                    "id": request.product_id,
                    "name": "Mock Product",
                    "price": 1999.0
                },
                "mock_mode": True
            }
        
        if not database_available or not db:
            # Mock product for testing
            mock_product = type('MockProduct', (), {
                'id': request.product_id,
                'name': 'Mock Product',
                'price': 1299.0,
                'description': 'สินค้าทดสอบระบบ AI Live Commerce'
            })()
            
            await live_orchestrator.present_product(
                product=mock_product,
                use_saved_script=request.use_saved_script
            )
            
            return {
                "success": True,
                "message": f"Presenting mock product: {mock_product.name}",
                "product": {
                    "id": mock_product.id,
                    "name": mock_product.name,
                    "price": mock_product.price
                }
            }
        
        # Real database query
        product = db.query(Product).filter(Product.id == request.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        await live_orchestrator.present_product(
            product=product,
            use_saved_script=request.use_saved_script
        )
        
        return {
            "success": True,
            "message": f"Presenting product: {product.name}",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Product presentation error: {e}")
        return {
            "success": False,
            "message": f"Product presentation failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

@router.get("/products/random")
async def present_random_product(db: Session = Depends(get_db) if database_available else None):
    """Present a random product"""
    try:
        if not live_orchestrator:
            # Mock random product
            import random
            mock_products = [
                {'id': '1', 'name': 'AI Smart Camera', 'price': 2999.0},
                {'id': '2', 'name': 'Wireless Earbuds Pro', 'price': 1599.0},
                {'id': '3', 'name': 'Smart Watch Ultra', 'price': 8999.0}
            ]
            selected = random.choice(mock_products)
            
            return {
                "success": True,
                "message": f"Mock: Presenting random product {selected['name']}",
                "product": selected,
                "mock_mode": True
            }
        
        if not database_available or not db:
            # Mock random product
            import random
            mock_products = [
                {'id': '1', 'name': 'AI Smart Camera', 'price': 2999.0, 'description': 'กล้องอัจฉริยะ AI ติดตามวัตถุอัตโนมัติ'},
                {'id': '2', 'name': 'Wireless Earbuds Pro', 'price': 1599.0, 'description': 'หูฟังไร้สาย เสียงใส ใช้งานได้ 24 ชม.'},
                {'id': '3', 'name': 'Smart Watch Ultra', 'price': 8999.0, 'description': 'นาฬิกาอัจฉริยะ ครบครันทุกฟีเจอร์'}
            ]
            
            selected = random.choice(mock_products)
            mock_product = type('MockProduct', (), selected)()
            
            await live_orchestrator.present_product(mock_product, use_saved_script=True)
            
            return {
                "success": True,
                "message": f"Presenting random product: {mock_product.name}",
                "product": {
                    "id": mock_product.id,
                    "name": mock_product.name,
                    "price": mock_product.price
                }
            }
        
        # Real database query
        import random
        products = db.query(Product).filter(Product.is_active == True).all()
        if not products:
            raise HTTPException(status_code=404, detail="No products available")
        
        product = random.choice(products)
        await live_orchestrator.present_product(product, use_saved_script=True)
        
        return {
            "success": True,
            "message": f"Presenting random product: {product.name}",
            "product": {
                "id": product.id,
                "name": product.name,
                "price": product.price
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Random product presentation error: {e}")
        return {
            "success": False,
            "message": f"Random product presentation failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

# AI control endpoints
@router.post("/auto-response")
async def set_auto_response(request: AutoResponseRequest):
    """Enable/disable AI auto-response to comments"""
    try:
        if not live_orchestrator:
            return {
                "success": True,
                "message": f"Mock: Auto-response {'enabled' if request.enabled else 'disabled'}",
                "enabled": request.enabled,
                "mock_mode": True
            }
        
        await live_orchestrator.set_auto_response(request.enabled)
        
        return {
            "success": True,
            "message": f"Auto-response {'enabled' if request.enabled else 'disabled'}",
            "enabled": request.enabled
        }
        
    except Exception as e:
        print(f"❌ Auto-response setting error: {e}")
        return {
            "success": False,
            "message": f"Auto-response setting failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

@router.post("/avatar/speak")
async def make_avatar_speak(request: CustomMessageRequest):
    """Make avatar speak custom message"""
    try:
        if not live_orchestrator:
            return {
                "success": True,
                "message": f"Mock: Avatar would say: {request.message}",
                "text": request.message,
                "mock_mode": True
            }
        
        await live_orchestrator.avatar_speak(request.message)
        
        # Also send to platform if specified
        if request.platform and live_orchestrator.current_platform:
            await live_orchestrator._send_platform_response(
                request.message, 
                request.platform or live_orchestrator.current_platform
            )
        
        return {
            "success": True,
            "message": "Avatar is speaking",
            "text": request.message
        }
        
    except Exception as e:
        print(f"❌ Avatar speak error: {e}")
        return {
            "success": False,
            "message": f"Avatar speak failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

# Testing endpoints
@router.post("/test/full-demo")
async def run_full_demo():
    """Run a full demonstration of the system"""
    try:
        if not live_orchestrator:
            return {
                "success": True,
                "message": "Mock: Full demo completed successfully",
                "session_status": {
                    "active": True,
                    "mock_mode": True,
                    "platform": "facebook"
                },
                "next_step": "Visit /avatar page to see avatar in action (Mock Mode)"
            }
        
        # Start session
        success = await live_orchestrator.start_live_session("facebook")
        if not success:
            raise HTTPException(status_code=500, detail="Could not start session")
        
        # Wait a bit
        import asyncio
        await asyncio.sleep(2)
        
        # Present a mock product
        mock_product = type('MockProduct', (), {
            'id': 'demo_product',
            'name': 'Demo Smart Device',
            'price': 1999.0,
            'description': 'อุปกรณ์อัจฉริยะสำหรับ Demo ระบบ AI Live Commerce'
        })()
        
        await live_orchestrator.present_product(mock_product, use_saved_script=False)
        
        await asyncio.sleep(2)
        
        # Custom avatar message
        await live_orchestrator.avatar_speak("ขอบคุณทุกคนที่ติดตามนะครับ! มีคำถามอะไรถามมาได้เลย")
        
        return {
            "success": True,
            "message": "Full demo completed successfully",
            "session_status": live_orchestrator.get_session_status(),
            "next_step": "Visit /avatar page to see avatar in action"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Full demo error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Full demo failed: {str(e)}",
            "error": str(e),
            "mock_mode": True
        }

# Analytics endpoints
@router.get("/analytics/session")
async def get_session_analytics():
    """Get session analytics"""
    try:
        if not live_orchestrator:
            return {
                "session_stats": {"mock_mode": True},
                "system_status": {
                    "integration_hub": False,
                    "avatar_service": False,
                    "facebook_service": False,
                    "ai_service": False,
                    "database_available": database_available
                }
            }
        
        return {
            "session_stats": live_orchestrator.get_session_status(),
            "system_status": {
                "integration_hub": True,
                "avatar_service": bool(live_orchestrator.avatar_controller),
                "facebook_service": bool(live_orchestrator.facebook_service),
                "ai_service": bool(live_orchestrator.ai_script_service),
                "database_available": database_available
            }
        }
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return {"error": str(e), "mock_mode": True}

# เพิ่มใน app/api/v1/integration.py

# เพิ่ม endpoints เหล่านี้ใน integration.py ของคุณ

@router.get("/speech/queue/status")
async def get_speech_queue_status():
    """Get current speech queue status - WORKING VERSION"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "queue_length": 0,
                "is_processing": False,
                "current_speech": None,
                "queue_items": []
            }
        
        # Use the real speech queue status
        avatar = live_orchestrator.avatar_controller
        if hasattr(avatar, 'speech_queue'):
            return avatar.speech_queue.get_queue_status()
        else:
            return {
                "queue_length": 0,
                "is_processing": False,
                "current_speech": None,
                "queue_items": []
            }
        
    except Exception as e:
        print(f"❌ Speech queue status error: {e}")
        return {
            "queue_length": 0,
            "is_processing": False,
            "error": str(e)
        }

@router.post("/speech/queue/clear")
async def clear_speech_queue(keep_high_priority: bool = True):
    """Clear speech queue"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "success": False,
                "message": "Avatar controller not available"
            }
        
        await live_orchestrator.avatar_controller.clear_speech_queue(keep_high_priority)
        
        return {
            "success": True,
            "message": f"Speech queue cleared {'(kept high priority)' if keep_high_priority else '(all cleared)'}"
        }
        
    except Exception as e:
        print(f"❌ Clear speech queue error: {e}")
        return {
            "success": False,
            "message": f"Failed to clear queue: {str(e)}"
        }

@router.post("/speech/interrupt")
async def interrupt_current_speech(request: CustomMessageRequest):
    """Interrupt current speech with urgent message"""
    try:
        if not live_orchestrator:
            return {
                "success": False,
                "message": "Integration hub not available"
            }
        
        if live_orchestrator.avatar_controller:
            await live_orchestrator.avatar_controller.speak_immediately(request.message)
        
        return {
            "success": True,
            "message": "Urgent speech interruption sent",
            "text": request.message
        }
        
    except Exception as e:
        print(f"❌ Speech interruption error: {e}")
        return {
            "success": False,
            "message": f"Interruption failed: {str(e)}"
        }

# อัปเดต run_full_demo endpoint
@router.post("/test/full-demo")
async def run_full_demo():
    """Run a full demonstration with proper speech queue management"""
    try:
        if not live_orchestrator:
            return {
                "success": True,
                "message": "Mock: Full demo completed successfully",
                "session_status": {
                    "active": True,
                    "mock_mode": True,
                    "platform": "facebook"
                },
                "next_step": "Visit /avatar page to see avatar in action (Mock Mode)"
            }
        
        # Use the enhanced demo function
        success = await live_orchestrator.run_full_demo()
        
        if success:
            return {
                "success": True,
                "message": "Full demo with speech queue started successfully",
                "session_status": live_orchestrator.get_session_status(),
                "next_step": "Visit /avatar page to see avatar in action",
                "speech_queue": live_orchestrator.avatar_controller.speech_queue.get_queue_status() if live_orchestrator.avatar_controller else {}
            }
        else:
            return {
                "success": False,
                "message": "Demo failed to start"
            }
        
    except Exception as e:
        print(f"❌ Full demo error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Full demo failed: {str(e)}",
            "error": str(e)
        }        


# เพิ่มใน app/api/v1/integration.py สำหรับ debug

@router.get("/debug/avatar-status")
async def debug_avatar_status():
    """Debug avatar service status"""
    try:
        debug_info = {
            "live_orchestrator_exists": live_orchestrator is not None,
            "avatar_controller_exists": False,
            "avatar_controller_type": None,
            "avatar_methods": [],
            "speech_queue_exists": False,
            "is_initialized": False
        }
        
        if live_orchestrator:
            debug_info["avatar_controller_exists"] = live_orchestrator.avatar_controller is not None
            
            if live_orchestrator.avatar_controller:
                avatar = live_orchestrator.avatar_controller
                debug_info["avatar_controller_type"] = type(avatar).__name__
                debug_info["avatar_methods"] = [method for method in dir(avatar) if not method.startswith('_')]
                debug_info["is_initialized"] = getattr(avatar, 'is_initialized', False)
                debug_info["speech_queue_exists"] = hasattr(avatar, 'speech_queue')
                
                # Check if it's the old or new avatar controller
                if hasattr(avatar, 'speech_queue'):
                    debug_info["speech_queue_type"] = type(avatar.speech_queue).__name__
                    debug_info["queue_methods"] = [method for method in dir(avatar.speech_queue) if not method.startswith('_')]
                else:
                    debug_info["old_avatar_controller"] = True
        
        return debug_info
        
    except Exception as e:
        return {
            "error": str(e),
            "traceback": str(e.__traceback__)
        }

@router.post("/debug/test-avatar-speak")
async def debug_test_avatar_speak():
    """Test avatar speak directly"""
    try:
        if not live_orchestrator:
            return {"error": "No live_orchestrator"}
            
        if not live_orchestrator.avatar_controller:
            return {"error": "No avatar_controller"}
        
        avatar = live_orchestrator.avatar_controller
        
        # Test different methods
        test_results = {}
        
        # Method 1: Direct speak method
        if hasattr(avatar, 'speak'):
            try:
                await avatar.speak("ทดสอบ speak method โดยตรง")
                test_results["direct_speak"] = "success"
            except Exception as e:
                test_results["direct_speak"] = f"error: {str(e)}"
        else:
            test_results["direct_speak"] = "method not found"
        
        # Method 2: Through orchestrator
        try:
            await live_orchestrator.avatar_speak("ทดสอบผ่าน orchestrator")
            test_results["orchestrator_speak"] = "success"
        except Exception as e:
            test_results["orchestrator_speak"] = f"error: {str(e)}"
        
        # Method 3: Check if speech queue is working
        if hasattr(avatar, 'speech_queue'):
            try:
                queue_status = avatar.speech_queue.get_queue_status()
                test_results["speech_queue_status"] = queue_status
            except Exception as e:
                test_results["speech_queue_status"] = f"error: {str(e)}"
        else:
            test_results["speech_queue_status"] = "speech_queue not found"
        
        return test_results
        
    except Exception as e:
        return {"error": str(e)}

@router.get("/debug/current-avatar-state")
async def debug_current_avatar_state():
    """Get current avatar state for debugging"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {"error": "Avatar controller not available"}
        
        avatar = live_orchestrator.avatar_controller
        
        state_info = {
            "avatar_type": type(avatar).__name__,
            "available_methods": [method for method in dir(avatar) if not method.startswith('_')],
            "is_initialized": getattr(avatar, 'is_initialized', 'unknown'),
            "has_speech_queue": hasattr(avatar, 'speech_queue'),
            "has_state": hasattr(avatar, 'state'),
        }
        
        # Try to get state
        if hasattr(avatar, 'get_state'):
            try:
                state_info["current_state"] = avatar.get_state()
            except Exception as e:
                state_info["get_state_error"] = str(e)
        
        # Check speech queue if exists
        if hasattr(avatar, 'speech_queue'):
            try:
                state_info["speech_queue_status"] = avatar.speech_queue.get_queue_status()
            except Exception as e:
                state_info["speech_queue_error"] = str(e)
        
        return state_info
        
    except Exception as e:
        return {"error": str(e)}        

# เพิ่มใน app/api/v1/integration.py

from pydantic import BaseModel
from typing import List

class ReorderQueueRequest(BaseModel):
    from_index: int
    to_index: int

class RemoveQueueItemRequest(BaseModel):
    index: int

@router.post("/speech/queue/remove")
async def remove_queue_item(request: RemoveQueueItemRequest):
    """Remove specific item from speech queue"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "success": False,
                "message": "Avatar controller not available"
            }
        
        # Get current queue
        queue = live_orchestrator.avatar_controller.speech_queue.queue
        
        if 0 <= request.index < len(queue):
            removed_item = queue.pop(request.index)
            return {
                "success": True,
                "message": f"Removed item: {removed_item.text[:30]}...",
                "removed_text": removed_item.text
            }
        else:
            return {
                "success": False,
                "message": "Invalid queue index"
            }
        
    except Exception as e:
        print(f"❌ Remove queue item error: {e}")
        return {
            "success": False,
            "message": f"Failed to remove item: {str(e)}"
        }

@router.post("/speech/queue/reorder")
async def reorder_queue_item(request: ReorderQueueRequest):
    """Reorder items in speech queue"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "success": False,
                "message": "Avatar controller not available"
            }
        
        queue = live_orchestrator.avatar_controller.speech_queue.queue
        
        # Validate indices
        if not (0 <= request.from_index < len(queue)):
            return {
                "success": False,
                "message": "Invalid from_index"
            }
        
        if not (0 <= request.to_index <= len(queue)):
            return {
                "success": False,
                "message": "Invalid to_index"
            }
        
        # Move item
        item = queue.pop(request.from_index)
        
        # Adjust to_index if moving forward
        if request.to_index > request.from_index:
            request.to_index -= 1
        
        queue.insert(request.to_index, item)
        
        return {
            "success": True,
            "message": f"Moved item from position {request.from_index + 1} to {request.to_index + 1}",
            "new_queue_length": len(queue)
        }
        
    except Exception as e:
        print(f"❌ Reorder queue error: {e}")
        return {
            "success": False,
            "message": f"Failed to reorder: {str(e)}"
        }

@router.get("/speech/queue/detailed-status")
async def get_detailed_queue_status():
    """Get detailed speech queue status with full item information"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "queue_length": 0,
                "is_processing": False,
                "current_speech": None,
                "queue_items": [],
                "error": "Avatar controller not available"
            }
        
        avatar = live_orchestrator.avatar_controller
        queue = avatar.speech_queue
        
        # Get detailed queue items
        detailed_items = []
        for i, item in enumerate(queue.queue):
            detailed_items.append({
                "index": i,
                "text": item.text,
                "priority": item.priority.name,
                "source": item.source,
                "duration": item.duration,
                "timestamp": item.timestamp,
                "estimated_time": i * 2.5  # Rough estimate
            })
        
        # Get current speech info
        current_speech_info = None
        if queue.current_speech:
            current_speech_info = {
                "text": queue.current_speech.text,
                "priority": queue.current_speech.priority.name,
                "source": queue.current_speech.source,
                "duration": queue.current_speech.duration
            }
        
        return {
            "queue_length": len(queue.queue),
            "is_processing": queue.is_processing,
            "current_speech": current_speech_info,
            "queue_items": detailed_items,
            "total_estimated_time": len(queue.queue) * 2.5,
            "avatar_initialized": avatar.is_initialized,
            "websocket_clients": len(avatar.websocket_clients)
        }
        
    except Exception as e:
        print(f"❌ Detailed queue status error: {e}")
        return {
            "queue_length": 0,
            "is_processing": False,
            "error": str(e)
        }

@router.post("/speech/queue/pause")
async def pause_speech_queue():
    """Pause speech queue processing"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "success": False,
                "message": "Avatar controller not available"
            }
        
        # Stop current speech and pause processing
        avatar = live_orchestrator.avatar_controller
        
        if hasattr(avatar.speech_queue, 'is_paused'):
            avatar.speech_queue.is_paused = True
        
        # Stop current speech
        if avatar.speech_queue.is_processing:
            await avatar._stop_current_speech()
        
        return {
            "success": True,
            "message": "Speech queue paused"
        }
        
    except Exception as e:
        print(f"❌ Pause queue error: {e}")
        return {
            "success": False,
            "message": f"Failed to pause: {str(e)}"
        }

@router.post("/speech/queue/resume")
async def resume_speech_queue():
    """Resume speech queue processing"""
    try:
        if not live_orchestrator or not live_orchestrator.avatar_controller:
            return {
                "success": False,
                "message": "Avatar controller not available"
            }
        
        avatar = live_orchestrator.avatar_controller
        
        if hasattr(avatar.speech_queue, 'is_paused'):
            avatar.speech_queue.is_paused = False
        
        return {
            "success": True,
            "message": "Speech queue resumed"
        }
        
    except Exception as e:
        print(f"❌ Resume queue error: {e}")
        return {
            "success": False,
            "message": f"Failed to resume: {str(e)}"
        }

@router.post("/speech/priority")
async def add_priority_speech(request: CustomMessageRequest):
    """Add speech with specific priority"""
    try:
        if not live_orchestrator:
            return {
                "success": False,
                "message": "Integration hub not available"
            }
        
        # Determine priority based on platform or add priority parameter
        priority_map = {
            "urgent": "URGENT",
            "high": "HIGH", 
            "normal": "NORMAL",
            "low": "LOW"
        }
        
        priority_str = priority_map.get(request.platform, "NORMAL")
        
        if live_orchestrator.avatar_controller and hasattr(live_orchestrator.avatar_controller, 'speak'):
            from app.services.avatar_service import SpeechPriority
            priority = getattr(SpeechPriority, priority_str, SpeechPriority.NORMAL)
            
            await live_orchestrator.avatar_controller.speak(
                text=request.message,
                priority=priority,
                source="priority_api"
            )
        else:
            await live_orchestrator.avatar_speak(request.message, source="priority_api")
        
        return {
            "success": True,
            "message": f"Added speech with {priority_str} priority",
            "text": request.message,
            "priority": priority_str
        }
        
    except Exception as e:
        print(f"❌ Priority speech error: {e}")
        return {
            "success": False,
            "message": f"Priority speech failed: {str(e)}"
        }        

