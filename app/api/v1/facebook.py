# app/api/v1/facebook.py - Updated for Real OAuth
"""
Facebook API Router with Real OAuth Integration
รองรับการเชื่อมต่อ Facebook จริงผ่าน OAuth 2.0
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/facebook", tags=["Facebook Integration"])

# Import service
try:
    from app.services.facebook_live_service import facebook_service
    print("✅ Facebook service imported in router")
except ImportError as e:
    print(f"⚠️ Facebook service import failed in router: {e}")
    facebook_service = None

# Pydantic Models
class FacebookPageSelect(BaseModel):
    page_id: str
    page_access_token: str

class LiveVideoCreate(BaseModel):
    title: str
    description: Optional[str] = ""

class FacebookComment(BaseModel):
    message: str

@router.get("/connect")
async def connect_facebook():
    """Initiate Facebook connection - Real OAuth or Mock"""
    try:
        if facebook_service:
            result = await facebook_service.connect_facebook()
            
            # If real connection, provide login URL
            if result.get("requires_auth") and result.get("login_url"):
                return {
                    **result,
                    "action": "redirect",
                    "instructions": [
                        "1. คลิกลิงก์ด้านล่างเพื่อเชื่อมต่อ Facebook",
                        "2. ล็อกอินและอนุญาตการเข้าถึง Pages",
                        "3. ระบบจะเปลี่ยนหน้าอัตโนมัติหลังจากเชื่อมต่อสำเร็จ"
                    ]
                }
            
            return result
        else:
            # Fallback mock connection
            return {
                "success": True,
                "mock_mode": True,
                "message": "Facebook connected successfully (Fallback Mock Mode)",
                "user_info": {
                    "id": "fallback_user_123",
                    "name": "Fallback User (Mock)"
                },
                "pages": [
                    {
                        "id": "fallback_page_123",
                        "name": "Fallback Shop (Mock)",
                        "access_token": "fallback_token_123",
                        "category": "Shopping & Retail",
                        "fan_count": 1000
                    }
                ]
            }
            
    except Exception as e:
        logger.error(f"Facebook connect error: {str(e)}")
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "fallback_available": True
        }

@router.get("/callback")
async def facebook_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """Handle Facebook OAuth callback"""
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"Facebook OAuth error: {error} - {error_description}")
            
            # Redirect to dashboard with error
            error_message = error_description or error
            return RedirectResponse(
                url=f"/?facebook_error={error_message}",
                status_code=302
            )
        
        # Check for required parameters
        if not code:
            logger.error("No authorization code received from Facebook")
            return RedirectResponse(
                url="/?facebook_error=No authorization code received",
                status_code=302
            )
        
        if not facebook_service:
            logger.error("Facebook service not available")
            return RedirectResponse(
                url="/?facebook_error=Facebook service not available",
                status_code=302
            )
        
        # Process the OAuth callback
        logger.info(f"Processing Facebook OAuth callback")
        result = await facebook_service.handle_oauth_callback(code, state)
        
        if result.get("success"):
            logger.info("Facebook OAuth successful, redirecting to dashboard")
            
            # Redirect to dashboard with success status
            return RedirectResponse(
                url="/?facebook_connected=true",
                status_code=302
            )
        else:
            error_msg = result.get("error", "Unknown error during OAuth")
            logger.error(f"Facebook OAuth failed: {error_msg}")
            
            return RedirectResponse(
                url=f"/?facebook_error={error_msg}",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"OAuth callback exception: {str(e)}")
        return RedirectResponse(
            url=f"/?facebook_error=OAuth callback failed: {str(e)}",
            status_code=302
        )

@router.get("/auth-status")
async def get_auth_status():
    """Get current authentication status (for AJAX polling)"""
    try:
        if facebook_service:
            status = facebook_service.get_connection_status()
            
            if status["connected"]:
                # Also get pages if connected
                pages_result = await facebook_service.get_user_pages()
                status["pages"] = pages_result.get("pages", [])
            
            return {
                "success": True,
                **status
            }
        else:
            return {
                "success": False,
                "connected": False,
                "error": "Facebook service not available"
            }
    except Exception as e:
        logger.error(f"Auth status check error: {str(e)}")
        return {
            "success": False,
            "connected": False,
            "error": str(e)
        }

@router.get("/status")
async def get_facebook_status():
    """Get Facebook connection status"""
    try:
        if facebook_service:
            return facebook_service.get_connection_status()
        else:
            return {
                "connected": False,
                "mock_mode": True,
                "error": "Facebook service not available",
                "user_info": None,
                "has_selected_page": False,
                "live_video_active": False
            }
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return {
            "connected": False,
            "error": str(e)
        }

@router.get("/pages")
async def get_facebook_pages():
    """Get user's Facebook pages"""
    try:
        if facebook_service:
            result = await facebook_service.get_user_pages()
            return result
        else:
            # Fallback pages
            return {
                "success": True,
                "pages": [
                    {
                        "id": "fallback_page_123",
                        "name": "Fallback Shop (Mock)",
                        "access_token": "fallback_token_123",
                        "category": "Shopping & Retail",
                        "fan_count": 1000
                    }
                ]
            }
    except Exception as e:
        logger.error(f"Get pages error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "pages": []
        }

@router.post("/select-page")
async def select_facebook_page(page_data: FacebookPageSelect):
    """Select a Facebook page for operations"""
    try:
        if facebook_service:
            result = await facebook_service.select_page(
                page_data.page_id, 
                page_data.page_access_token
            )
            return result
        else:
            # Fallback selection
            return {
                "success": True,
                "selected_page": {
                    "id": page_data.page_id,
                    "name": "Selected Page (Fallback Mock)",
                    "access_token": page_data.page_access_token
                },
                "message": "Page selected successfully (Fallback Mode)"
            }
    except Exception as e:
        logger.error(f"Select page error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/live/create")
async def create_live_video(live_data: LiveVideoCreate):
    """Create a Facebook Live Video"""
    try:
        if facebook_service:
            result = await facebook_service.create_live_video(
                live_data.title, 
                live_data.description
            )
            return result
        else:
            # Fallback live video creation
            import secrets
            from datetime import datetime
            
            live_video = {
                "id": f"fallback_live_{secrets.token_hex(8)}",
                "title": live_data.title,
                "description": live_data.description,
                "status": "LIVE",
                "permalink_url": f"https://facebook.com/fallback/videos/fallback_{secrets.token_hex(8)}",
                "stream_url": f"rtmps://live-api-s.facebook.com:443/rtmp/fallback_{secrets.token_hex(8)}",
                "stream_key": f"fallback_key_{secrets.token_hex(16)}",
                "mock_mode": True,
                "created_time": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "live_video": live_video,
                "message": "Live video created successfully (Fallback Mode)"
            }
            
    except Exception as e:
        logger.error(f"Create live video error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/live/end")
async def end_live_video():
    """End current Facebook Live Video"""
    try:
        if facebook_service:
            result = await facebook_service.end_live_video()
            return result
        else:
            return {
                "success": True,
                "message": "Live video ended successfully (Fallback Mode)"
            }
    except Exception as e:
        logger.error(f"End live video error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/live/comments")
async def get_live_comments():
    """Get comments from current live video"""
    try:
        if facebook_service:
            result = await facebook_service.get_live_comments()
            return result
        else:
            # Fallback mock comments
            import random
            import secrets
            from datetime import datetime
            
            if random.random() < 0.3:  # 30% chance
                mock_comments = [
                    {
                        "id": f"fallback_comment_{secrets.token_hex(8)}",
                        "message": "สินค้าดีมาก ราคาเท่าไหร่ครับ?",
                        "from": {"id": "fallback_user_1", "name": "ลูกค้า A (Fallback)"},
                        "created_time": datetime.now().isoformat()
                    }
                ]
                return {
                    "success": True,
                    "comments": [random.choice(mock_comments)]
                }
            
            return {"success": True, "comments": []}
            
    except Exception as e:
        logger.error(f"Get comments error: {str(e)}")
        return {"success": True, "comments": []}

@router.post("/live/comment")
async def post_live_comment(comment_data: FacebookComment):
    """Post a comment to current live video"""
    try:
        if facebook_service:
            result = await facebook_service.post_comment(comment_data.message)
            return result
        else:
            import secrets
            return {
                "success": True,
                "comment_id": f"fallback_comment_{secrets.token_hex(8)}",
                "message": "Comment posted successfully (Fallback Mode)"
            }
    except Exception as e:
        logger.error(f"Post comment error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/live/info")
async def get_live_info():
    """Get current live video information"""
    try:
        if facebook_service and facebook_service.current_live_video:
            return {
                "success": True,
                "live_video": facebook_service.current_live_video,
                "mock_mode": facebook_service.mock_mode
            }
        else:
            return {
                "success": False,
                "error": "No active live video"
            }
    except Exception as e:
        logger.error(f"Get live info error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/health")
async def facebook_health():
    """Facebook integration health check"""
    try:
        if facebook_service:
            return facebook_service.get_health_status()
        else:
            return {
                "status": "limited",
                "message": "Facebook service not available - using fallback mode",
                "mock_mode": True,
                "facebook_app_configured": False
            }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

# Additional endpoints for debugging
@router.get("/debug/config")
async def debug_facebook_config():
    """Debug Facebook configuration (development only)"""
    try:
        import os
        
        config_info = {
            "app_id_configured": bool(os.getenv("FACEBOOK_APP_ID")),
            "app_secret_configured": bool(os.getenv("FACEBOOK_APP_SECRET")),
            "redirect_uri": os.getenv("FACEBOOK_REDIRECT_URI", "Not set"),
            "api_version": os.getenv("FACEBOOK_API_VERSION", "v18.0"),
            "mock_mode": os.getenv("FACEBOOK_MOCK_MODE", "true"),
            "service_available": facebook_service is not None
        }
        
        if facebook_service:
            config_info.update({
                "service_mock_mode": facebook_service.mock_mode,
                "service_connected": facebook_service.is_connected,
                "has_access_token": bool(facebook_service.access_token),
                "selected_page": facebook_service.selected_page.get("name") if facebook_service.selected_page else None
            })
        
        return {
            "success": True,
            "config": config_info
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/debug/force-mock")
async def force_mock_mode():
    """Force mock mode (development only)"""
    try:
        if facebook_service:
            facebook_service.mock_mode = True
            result = await facebook_service._mock_connect()
            
            return {
                "success": True,
                "message": "Forced mock mode enabled",
                "result": result
            }
        else:
            return {
                "success": False,
                "error": "Facebook service not available"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }