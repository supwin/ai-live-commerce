"""
Mobile Live Streaming API Endpoints
Handles TikTok live streaming via mobile screen mirroring
"""

import asyncio
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional, List
from pydantic import BaseModel

try:
    from app.services.mobile_mirror_service import mobile_mirror_service
except ImportError:
    mobile_mirror_service = None

try:
    from app.services.ai_script_service import ai_script_service
except ImportError:
    ai_script_service = None

import logging
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/mobile-live", tags=["Mobile Live Streaming"])

# Request Models
class MirrorConfig(BaseModel):
    device_id: Optional[str] = None
    wireless: bool = False
    quality: str = "medium"

class ContentUpdate(BaseModel):
    video_path: Optional[str] = None
    product_info: Optional[dict] = None

class LiveSession(BaseModel):
    product_ids: List[str]
    session_duration: int = 1800
    content_interval: int = 300

@router.get("/test")
async def test_mobile_live():
    """Test endpoint for mobile live API"""
    return {
        "message": "Mobile live API working",
        "status": "ok",
        "services": {
            "mobile_mirror": mobile_mirror_service is not None,
            "ai_script": ai_script_service is not None
        }
    }

@router.get("/status")
async def get_mobile_live_status():
    """Get mobile live streaming status"""
    if not mobile_mirror_service:
        return {
            "mobile_mirroring": {"active": False},
            "content_display": {"server_running": False},
            "system_ready": False,
            "error": "Mobile mirror service not available"
        }
    
    try:
        status = await mobile_mirror_service.get_mirror_status()
        return {
            "mobile_mirroring": {
                "active": status["is_mirroring"],
                "device_connected": status["device_connected"],
                "device_ip": status["device_ip"],
                "method": status["mirror_method"],
                "quality": status["mirror_quality"]
            },
            "content_display": {
                "server_running": status["content_server_running"],
                "server_url": status["content_server_url"],
                "current_content": status["current_content"]
            },
            "system_ready": status["is_mirroring"] and status["content_server_running"],
            "tiktok_live_ready": status["device_connected"]
        }
    except Exception as e:
        return {
            "mobile_mirroring": {"active": False},
            "content_display": {"server_running": False},
            "system_ready": False,
            "error": str(e)
        }

@router.get("/setup-guide")
async def get_mobile_setup_guide():
    """Get setup guide for mobile live streaming"""
    
    guide_html = """<!DOCTYPE html>
<html>
<head>
    <title>Mobile TikTok Live Setup Guide</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        .step { background: #e9ecef; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Mobile TikTok Live Setup Guide</h1>
        <p>Complete guide for AI-powered live streaming via mobile screen mirroring.</p>
        
        <div class="step">
            <h3>Step 1: Connect Android Device</h3>
            <ul>
                <li>Enable Developer Options (tap Build Number 7 times)</li>
                <li>Enable USB Debugging in Developer Options</li>
                <li>Connect phone to computer via USB</li>
            </ul>
            <a href="/api/v1/mobile-live/detect-devices" class="btn">🔍 Detect Devices</a>
        </div>
        
        <div class="step">
            <h3>Step 2: Setup Screen Mirroring</h3>
            <ul>
                <li>Install scrcpy (screen copy tool)</li>
                <li>Setup mirroring configuration</li>
                <li>Test screen mirroring</li>
            </ul>
            <a href="/api/v1/mobile-live/dashboard" class="btn">🎛️ Mobile Dashboard</a>
        </div>
        
        <div class="step">
            <h3>Step 3: Start Live Streaming</h3>
            <ul>
                <li>Start content display server</li>
                <li>Open TikTok app on phone</li>
                <li>Point camera at computer screen</li>
                <li>Start TikTok Live</li>
            </ul>
            <a href="/api/v1/mobile-live/test" class="btn">🧪 Test API</a>
        </div>
        
        <p style="text-align: center; margin-top: 30px;">
            <a href="/docs">📚 API Documentation</a> | 
            <a href="/api/v1/mobile-live/status">📊 Status</a>
        </p>
    </div>
</body>
</html>"""
    
    return HTMLResponse(content=guide_html)

@router.get("/detect-devices")
async def detect_mobile_devices():
    """Detect connected mobile devices"""
    if not mobile_mirror_service:
        raise HTTPException(status_code=503, detail="Mobile mirror service not available")
    
    try:
        result = await mobile_mirror_service.detect_devices()
        return {
            "success": result["success"],
            "devices": result["devices"],
            "recommendations": result.get("recommendations", [])
        }
    except Exception as e:
        print("ERROR: "f"Device detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Device detection failed: {str(e)}")

@router.post("/start-display-server")
async def start_content_display_server():
    """Start web server for displaying AI content"""
    if not mobile_mirror_service:
        raise HTTPException(status_code=503, detail="Mobile mirror service not available")
    
    try:
        result = await mobile_mirror_service.start_content_display_server()
        return {
            "success": result["success"],
            "message": result["message"],
            "server_info": result
        }
    except Exception as e:
        print("ERROR: "f"Failed to start display server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Display server failed: {str(e)}")

@router.post("/update-content")
async def update_display_content(content: ContentUpdate):
    """Update content being displayed for mobile capture"""
    if not mobile_mirror_service:
        raise HTTPException(status_code=503, detail="Mobile mirror service not available")
    
    try:
        result = await mobile_mirror_service.update_display_content(
            video_path=content.video_path,
            product_info=content.product_info
        )
        return {
            "success": result["success"],
            "message": result["message"],
            "updated_content": result.get("content")
        }
    except Exception as e:
        print("ERROR: "f"Failed to update content: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Content update failed: {str(e)}")

@router.get("/dashboard")
async def get_mobile_live_dashboard():
    """Get mobile live streaming dashboard"""
    
    dashboard_html = """<!DOCTYPE html>
<html>
<head>
    <title>Mobile Live Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .btn { display: inline-block; padding: 10px 20px; margin: 5px; background: #007bff; color: white; text-decoration: none; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-active { background-color: #28a745; }
        .status-offline { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Mobile TikTok Live Dashboard</h1>
            <p>AI-Powered Live Commerce via Screen Mirroring</p>
        </div>
        
        <div class="cards">
            <div class="card">
                <h3><span class="status-indicator status-offline" id="mirror-status"></span>Screen Mirroring</h3>
                <p>Status: <span id="mirror-text">Checking...</span></p>
                <button class="btn btn-success" onclick="startMirroring()">📱 Start Mirroring</button>
                <button class="btn" onclick="detectDevices()">🔍 Detect Devices</button>
            </div>
            
            <div class="card">
                <h3><span class="status-indicator status-offline" id="display-status"></span>Content Display</h3>
                <p>Server: <span id="display-text">Offline</span></p>
                <button class="btn btn-success" onclick="startDisplayServer()">🖥️ Start Server</button>
                <button class="btn" onclick="updateContent()">🔄 Update Content</button>
            </div>
            
            <div class="card">
                <h3>🎯 TikTok Live Status</h3>
                <p>Ready for mobile streaming</p>
                <a href="https://www.tiktok.com" target="_blank" class="btn">📱 Open TikTok</a>
                <button class="btn" onclick="refreshStatus()">🔄 Refresh</button>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <p><strong>Instructions:</strong></p>
            <p>1. Connect Android device → 2. Start mirroring → 3. Start display server → 4. Open TikTok Live</p>
        </div>
    </div>
    
    <script>
        async function refreshStatus() {
            try {
                const response = await fetch('/api/v1/mobile-live/status');
                const data = await response.json();
                
                document.getElementById('mirror-text').textContent = 
                    data.mobile_mirroring.active ? 'Active' : 'Offline';
                document.getElementById('mirror-status').className = 
                    'status-indicator ' + (data.mobile_mirroring.active ? 'status-active' : 'status-offline');
                
                document.getElementById('display-text').textContent = 
                    data.content_display.server_running ? 'Running' : 'Offline';
                document.getElementById('display-status').className = 
                    'status-indicator ' + (data.content_display.server_running ? 'status-active' : 'status-offline');
            } catch (error) {
                console.error('Status refresh failed:', error);
            }
        }
        
        async function detectDevices() {
            try {
                const response = await fetch('/api/v1/mobile-live/detect-devices');
                const data = await response.json();
                alert(`Devices found: ${data.devices.total_count}`);
            } catch (error) {
                alert('Device detection failed');
            }
        }
        
        async function startDisplayServer() {
            try {
                const response = await fetch('/api/v1/mobile-live/start-display-server', {
                    method: 'POST'
                });
                const data = await response.json();
                alert(data.success ? 'Display server started' : 'Failed to start server');
                refreshStatus();
            } catch (error) {
                alert('Server start failed');
            }
        }
        
        async function updateContent() {
            try {
                const response = await fetch('/api/v1/mobile-live/update-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_info: {
                            name: 'AI Smart Device',
                            price: '$199',
                            description: 'AI-powered smart device demo'
                        }
                    })
                });
                const data = await response.json();
                alert(data.success ? 'Content updated' : 'Update failed');
            } catch (error) {
                alert('Content update failed');
            }
        }
        
        function startMirroring() {
            alert('Start mirroring - connect your Android device first');
        }
        
        // Auto-refresh every 10 seconds
        setInterval(refreshStatus, 10000);
        refreshStatus();
    </script>
</body>
</html>"""
    
    return HTMLResponse(content=dashboard_html)