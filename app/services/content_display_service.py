# app/services/content_display_service.py
"""
Enhanced Content Display Service - Step 2 Implementation
แสดงเนื้อหา AI-generated real-time สำหรับ mobile camera capture
รองรับ WebSocket updates, 9:16 format, high contrast
"""

import asyncio
import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import socket
from contextlib import asynccontextmanager

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Local imports
from app.core.config import get_settings

class ContentDisplayService:
    """Enhanced Content Display Service สำหรับ real-time content display"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Server configuration
        self.display_config = {
            "host": "0.0.0.0",
            "port": 8080,           # Display server port
            "width": 1080,          # TikTok 9:16 width  
            "height": 1920,         # TikTok 9:16 height
            "auto_refresh": True,   # Auto refresh content
            "refresh_interval": 5,  # Seconds
            "high_contrast": True   # High contrast for camera
        }
        
        # Content management
        self.current_content = {
            "video_path": None,
            "product_info": None,
            "script_info": None,
            "updated_at": None,
            "display_mode": "video"  # video, slideshow, text
        }
        
        # WebSocket connections
        self.active_connections: List[WebSocket] = []
        
        # Directories
        self.static_dir = Path("frontend/static")
        self.display_dir = Path("frontend/live_display")
        self.video_dir = Path("frontend/uploads/videos")
        
        # Create directories
        for directory in [self.display_dir, self.static_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Server status
        self.server_process = None
        self.is_running = False
        
        print(f"🖥️ Content Display Service initialized")
        print(f"   📐 Format: {self.display_config['width']}x{self.display_config['height']} (9:16)")
        print(f"   🌐 Server: {self.display_config['host']}:{self.display_config['port']}")
        print(f"   📁 Display pages: {self.display_dir}")
        print(f"   🎬 Video source: {self.video_dir}")
    
    async def start_display_server(self) -> Dict[str, Any]:
        """เริ่ม content display server"""
        
        try:
            print("🚀 Starting content display server...")
            
            # ตรวจสอบ port
            if self._is_port_in_use(self.display_config["port"]):
                return {
                    "success": False,
                    "error": f"Port {self.display_config['port']} already in use",
                    "port": self.display_config["port"]
                }
            
            # สร้าง display pages
            await self._create_display_pages()
            
            # สร้าง FastAPI app สำหรับ display
            display_app = await self._create_display_app()
            
            # เริ่ม server ใน background
            config = uvicorn.Config(
                display_app,
                host=self.display_config["host"],
                port=self.display_config["port"],
                log_level="error"  # Reduce log noise
            )
            
            self.server_process = uvicorn.Server(config)
            
            # Start server in background task
            asyncio.create_task(self.server_process.serve())
            
            # Wait a moment for server to start
            await asyncio.sleep(1)
            
            self.is_running = True
            
            server_url = f"http://localhost:{self.display_config['port']}"
            
            return {
                "success": True,
                "message": "Content display server started",
                "server_url": server_url,
                "port": self.display_config["port"],
                "display_pages": {
                    "main": f"{server_url}/",
                    "fullscreen": f"{server_url}/fullscreen",
                    "mobile": f"{server_url}/mobile"
                },
                "features": [
                    "Real-time content updates via WebSocket",
                    "9:16 aspect ratio optimized for TikTok",
                    "High contrast mode for camera capture",
                    "Auto-refresh content every 5 seconds",
                    "Multiple display modes (video, slideshow, text)"
                ]
            }
            
        except Exception as e:
            print(f"❌ Failed to start display server: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_display_app(self) -> FastAPI:
        """สร้าง FastAPI app สำหรับ display server"""
        
        app = FastAPI(title="AI Content Display Server")
        
        # Mount static files
        app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        app.mount("/videos", StaticFiles(directory=str(self.video_dir)), name="videos")
        
        # WebSocket endpoint
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connect_websocket(websocket)
            try:
                while True:
                    # Keep connection alive
                    await websocket.receive_text()
            except WebSocketDisconnect:
                await self.disconnect_websocket(websocket)
        
        # Main display page
        @app.get("/", response_class=HTMLResponse)
        async def display_main():
            return await self._get_main_display_page()
        
        # Fullscreen display
        @app.get("/fullscreen", response_class=HTMLResponse)
        async def display_fullscreen():
            return await self._get_fullscreen_display_page()
        
        # Mobile optimized display
        @app.get("/mobile", response_class=HTMLResponse)
        async def display_mobile():
            return await self._get_mobile_display_page()
        
        # API endpoints
        @app.get("/api/current-content")
        async def get_current_content():
            return {
                "success": True,
                "content": self.current_content,
                "server_time": datetime.utcnow().isoformat()
            }
        
        @app.post("/api/update-content")
        async def update_content_api(content_data: dict):
            result = await self.update_content(content_data)
            return result
        
        @app.get("/api/status")
        async def get_display_status():
            return {
                "success": True,
                "server_running": self.is_running,
                "active_connections": len(self.active_connections),
                "current_content": self.current_content,
                "display_config": self.display_config
            }
        
        return app
    
    async def _create_display_pages(self):
        """สร้าง HTML pages สำหรับ display"""
        
        # Main display page
        main_page_path = self.display_dir / "index.html"
        with open(main_page_path, 'w', encoding='utf-8') as f:
            f.write(await self._get_main_display_html())
        
        # Fullscreen page
        fullscreen_page_path = self.display_dir / "fullscreen.html"
        with open(fullscreen_page_path, 'w', encoding='utf-8') as f:
            f.write(await self._get_fullscreen_display_html())
        
        # Mobile page
        mobile_page_path = self.display_dir / "mobile.html"
        with open(mobile_page_path, 'w', encoding='utf-8') as f:
            f.write(await self._get_mobile_display_html())
        
        print(f"✅ Display pages created in {self.display_dir}")
    
    async def _get_main_display_page(self) -> str:
        """Main display page สำหรับ desktop viewing"""
        return await self._get_main_display_html()
    
    async def _get_fullscreen_display_page(self) -> str:
        """Fullscreen display สำหรับ presentation"""
        return await self._get_fullscreen_display_html()
    
    async def _get_mobile_display_page(self) -> str:
        """Mobile-optimized display สำหรับ camera capture"""
        return await self._get_mobile_display_html()
    
    async def _get_main_display_html(self) -> str:
        """สร้าง HTML สำหรับ main display"""
        
        return f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Live Commerce - Content Display</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            overflow: hidden;
            height: 100vh;
        }}
        
        .display-container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        
        .content-frame {{
            width: 60vh;  /* 9:16 aspect ratio */
            height: 100vh;
            background: #000;
            border: 3px solid #fff;
            border-radius: 20px;
            overflow: hidden;
            position: relative;
            box-shadow: 0 0 30px rgba(255,255,255,0.3);
        }}
        
        .video-container {{
            width: 100%;
            height: 100%;
            position: relative;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .video-player {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .content-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.8));
            padding: 30px 20px 20px;
            color: white;
        }}
        
        .product-name {{
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 8px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        
        .product-price {{
            font-size: 32px;
            color: #ff6b6b;
            font-weight: bold;
            margin-bottom: 8px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        
        .product-description {{
            font-size: 16px;
            opacity: 0.9;
            line-height: 1.4;
        }}
        
        .live-indicator {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: #ff0000;
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
            animation: pulse 2s infinite;
        }}
        
        .status-panel {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 10px;
            min-width: 200px;
        }}
        
        .status-item {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 5px;
            font-size: 14px;
        }}
        
        .placeholder-content {{
            text-align: center;
            padding: 40px 20px;
        }}
        
        .placeholder-title {{
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
        
        .placeholder-subtitle {{
            font-size: 24px;
            opacity: 0.8;
            margin-bottom: 30px;
        }}
        
        .placeholder-instructions {{
            font-size: 18px;
            opacity: 0.7;
            line-height: 1.6;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease-out;
        }}
        
        .controls-hint {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.7);
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 14px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="display-container">
        <div class="content-frame">
            <div class="live-indicator">🔴 LIVE</div>
            
            <div class="video-container" id="videoContainer">
                <!-- Video content will be loaded here -->
                <div class="placeholder-content fade-in">
                    <div class="placeholder-title">🤖 AI Live Commerce</div>
                    <div class="placeholder-subtitle">Content Display Ready</div>
                    <div class="placeholder-instructions">
                        Content will appear here automatically<br>
                        Point your mobile camera at this area<br>
                        Perfect for TikTok Live streaming
                    </div>
                </div>
            </div>
            
            <div class="content-overlay" id="contentOverlay" style="display: none;">
                <div class="product-name" id="productName">Product Name</div>
                <div class="product-price" id="productPrice">฿0</div>
                <div class="product-description" id="productDescription">Product description</div>
            </div>
        </div>
        
        <div class="status-panel">
            <div class="status-item">
                <span>🔗 WebSocket:</span>
                <span id="websocketStatus">Connecting...</span>
            </div>
            <div class="status-item">
                <span>📱 Format:</span>
                <span>9:16 (TikTok)</span>
            </div>
            <div class="status-item">
                <span>🔄 Updates:</span>
                <span id="updateCount">0</span>
            </div>
            <div class="status-item">
                <span>⏰ Last Update:</span>
                <span id="lastUpdate">Never</span>
            </div>
        </div>
        
        <div class="controls-hint">
            Press F11 for fullscreen • /mobile for mobile view
        </div>
    </div>
    
    <script>
        let ws = null;
        let updateCount = 0;
        let currentContent = null;
        
        // WebSocket connection
        function connectWebSocket() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {{
                document.getElementById('websocketStatus').textContent = 'Connected';
                document.getElementById('websocketStatus').style.color = '#4ade80';
                console.log('WebSocket connected');
            }};
            
            ws.onmessage = function(event) {{
                try {{
                    const data = JSON.parse(event.data);
                    handleContentUpdate(data);
                }} catch (error) {{
                    console.error('WebSocket message error:', error);
                }}
            }};
            
            ws.onclose = function() {{
                document.getElementById('websocketStatus').textContent = 'Disconnected';
                document.getElementById('websocketStatus').style.color = '#ef4444';
                console.log('WebSocket disconnected');
                
                // Reconnect after 3 seconds
                setTimeout(connectWebSocket, 3000);
            }};
            
            ws.onerror = function(error) {{
                console.error('WebSocket error:', error);
            }};
        }}
        
        // Handle content updates
        function handleContentUpdate(data) {{
            console.log('Content update received:', data);
            
            updateCount++;
            document.getElementById('updateCount').textContent = updateCount;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            
            if (data.type === 'content_update') {{
                updateDisplayContent(data.content);
            }}
        }}
        
        // Update display content
        function updateDisplayContent(content) {{
            const videoContainer = document.getElementById('videoContainer');
            const contentOverlay = document.getElementById('contentOverlay');
            
            if (content.video_path) {{
                // Show video content
                videoContainer.innerHTML = `
                    <video class="video-player fade-in" autoplay loop muted>
                        <source src="${{content.video_path}}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>
                `;
            }} else {{
                // Show placeholder or text content
                videoContainer.innerHTML = `
                    <div class="placeholder-content fade-in">
                        <div class="placeholder-title">🎬 Content Ready</div>
                        <div class="placeholder-subtitle">${{content.product_info?.name || 'AI Generated Content'}}</div>
                        <div class="placeholder-instructions">
                            ${{content.product_info?.description || 'Live streaming content'}}
                        </div>
                    </div>
                `;
            }}
            
            // Update overlay information
            if (content.product_info) {{
                document.getElementById('productName').textContent = content.product_info.name || 'Product';
                document.getElementById('productPrice').textContent = content.product_info.price || '฿0';
                document.getElementById('productDescription').textContent = content.product_info.description || '';
                contentOverlay.style.display = 'block';
            }} else {{
                contentOverlay.style.display = 'none';
            }}
            
            currentContent = content;
        }}
        
        // Fetch current content
        async function fetchCurrentContent() {{
            try {{
                const response = await fetch('/api/current-content');
                const data = await response.json();
                
                if (data.success && data.content) {{
                    updateDisplayContent(data.content);
                }}
            }} catch (error) {{
                console.error('Failed to fetch current content:', error);
            }}
        }}
        
        // Auto-refresh content every 5 seconds (fallback)
        setInterval(fetchCurrentContent, 5000);
        
        // Initialize
        connectWebSocket();
        fetchCurrentContent();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'F11') {{
                event.preventDefault();
                if (document.fullscreenElement) {{
                    document.exitFullscreen();
                }} else {{
                    document.documentElement.requestFullscreen();
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    async def _get_fullscreen_display_html(self) -> str:
        """สร้าง HTML สำหรับ fullscreen display"""
        
        return f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Live Commerce - Fullscreen Display</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial', sans-serif;
            background: #000;
            color: white;
            overflow: hidden;
            height: 100vh;
        }}
        
        .fullscreen-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        
        .content-display {{
            width: 100vh;  /* 9:16 aspect ratio */
            height: 100vh;
            background: #000;
            position: relative;
            overflow: hidden;
        }}
        
        .video-player {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .content-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.9));
            padding: 40px 30px 30px;
            color: white;
        }}
        
        .product-name {{
            font-size: 42px;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
        }}
        
        .product-price {{
            font-size: 48px;
            color: #ff6b6b;
            font-weight: bold;
            margin-bottom: 15px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
        }}
        
        .product-description {{
            font-size: 24px;
            opacity: 0.9;
            line-height: 1.4;
        }}
        
        .live-indicator {{
            position: absolute;
            top: 30px;
            left: 30px;
            background: #ff0000;
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 18px;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
            100% {{ opacity: 1; }}
        }}
        
        .placeholder-content {{
            text-align: center;
            padding: 60px 40px;
        }}
        
        .placeholder-title {{
            font-size: 72px;
            margin-bottom: 30px;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.8);
        }}
        
        .placeholder-subtitle {{
            font-size: 36px;
            opacity: 0.8;
            margin-bottom: 40px;
        }}
        
        .placeholder-instructions {{
            font-size: 24px;
            opacity: 0.7;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="fullscreen-container">
        <div class="content-display">
            <div class="live-indicator">🔴 LIVE</div>
            
            <div id="videoContainer">
                <div class="placeholder-content">
                    <div class="placeholder-title">🤖 AI Live Commerce</div>
                    <div class="placeholder-subtitle">Fullscreen Display</div>
                    <div class="placeholder-instructions">
                        Ready for TikTok Live streaming<br>
                        Point your camera at this screen
                    </div>
                </div>
            </div>
            
            <div class="content-overlay" id="contentOverlay" style="display: none;">
                <div class="product-name" id="productName">Product Name</div>
                <div class="product-price" id="productPrice">฿0</div>
                <div class="product-description" id="productDescription">Product description</div>
            </div>
        </div>
    </div>
    
    <script>
        // WebSocket and content update logic (similar to main display)
        let ws = null;
        
        function connectWebSocket() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {{
                console.log('WebSocket connected');
            }};
            
            ws.onmessage = function(event) {{
                try {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'content_update') {{
                        updateDisplayContent(data.content);
                    }}
                }} catch (error) {{
                    console.error('WebSocket message error:', error);
                }}
            }};
            
            ws.onclose = function() {{
                setTimeout(connectWebSocket, 3000);
            }};
        }}
        
        function updateDisplayContent(content) {{
            const videoContainer = document.getElementById('videoContainer');
            const contentOverlay = document.getElementById('contentOverlay');
            
            if (content.video_path) {{
                videoContainer.innerHTML = `
                    <video class="video-player" autoplay loop muted>
                        <source src="${{content.video_path}}" type="video/mp4">
                    </video>
                `;
            }} else {{
                videoContainer.innerHTML = `
                    <div class="placeholder-content">
                        <div class="placeholder-title">🎬 Content Ready</div>
                        <div class="placeholder-subtitle">${{content.product_info?.name || 'AI Generated Content'}}</div>
                        <div class="placeholder-instructions">
                            ${{content.product_info?.description || 'Live streaming content'}}
                        </div>
                    </div>
                `;
            }}
            
            if (content.product_info) {{
                document.getElementById('productName').textContent = content.product_info.name || '';
                document.getElementById('productPrice').textContent = content.product_info.price || '';
                document.getElementById('productDescription').textContent = content.product_info.description || '';
                contentOverlay.style.display = 'block';
            }} else {{
                contentOverlay.style.display = 'none';
            }}
        }}
        
        async function fetchCurrentContent() {{
            try {{
                const response = await fetch('/api/current-content');
                const data = await response.json();
                if (data.success && data.content) {{
                    updateDisplayContent(data.content);
                }}
            }} catch (error) {{
                console.error('Failed to fetch current content:', error);
            }}
        }}
        
        connectWebSocket();
        fetchCurrentContent();
        setInterval(fetchCurrentContent, 5000);
        
        // Auto fullscreen
        document.documentElement.requestFullscreen().catch(() => {{}});
    </script>
</body>
</html>"""
    
    async def _get_mobile_display_html(self) -> str:
        """สร้าง HTML สำหรับ mobile display (optimized for camera capture)"""
        
        return f"""<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Live Commerce - Mobile Display</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Arial Black', sans-serif;
            background: #000;
            color: #fff;
            overflow: hidden;
            height: 100vh;
            width: 100vw;
        }}
        
        .mobile-container {{
            width: 60vh;  /* 9:16 aspect ratio */
            height: 100vh;
            position: relative;
            background: linear-gradient(45deg, #000 0%, #1a1a1a 100%);
        }}
        
        .content-area {{
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }}
        
        .video-player {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}
        
        .product-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, #000);
            padding: 60px 40px 40px;
            text-align: center;
        }}
        
        .product-name {{
            font-size: 48px;
            font-weight: 900;
            margin-bottom: 20px;
            text-shadow: 4px 4px 8px rgba(0,0,0,0.9);
            line-height: 1.2;
            color: #fff;
        }}
        
        .product-price {{
            font-size: 64px;
            color: #00ff00;
            font-weight: 900;
            margin-bottom: 20px;
            text-shadow: 4px 4px 8px rgba(0,0,0,0.9);
            animation: priceGlow 2s infinite alternate;
        }}
        
        @keyframes priceGlow {{
            from {{ text-shadow: 4px 4px 8px rgba(0,0,0,0.9), 0 0 10px #00ff00; }}
            to {{ text-shadow: 4px 4px 8px rgba(0,0,0,0.9), 0 0 20px #00ff00, 0 0 30px #00ff00; }}
        }}
        
        .product-description {{
            font-size: 28px;
            opacity: 0.9;
            line-height: 1.4;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.9);
            max-width: 80%;
        }}
        
        .live-badge {{
            position: absolute;
            top: 40px;
            left: 40px;
            background: #ff0000;
            color: white;
            padding: 16px 32px;
            border-radius: 30px;
            font-weight: 900;
            font-size: 24px;
            animation: livePulse 1.5s infinite;
            box-shadow: 0 0 20px rgba(255,0,0,0.5);
        }}
        
        @keyframes livePulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
            100% {{ transform: scale(1); }}
        }}
        
        .qr-corner {{
            position: absolute;
            top: 40px;
            right: 40px;
            width: 120px;
            height: 120px;
            background: #fff;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            color: #000;
            font-weight: bold;
            box-shadow: 0 0 20px rgba(255,255,255,0.3);
        }}
        
        .placeholder-mobile {{
            text-align: center;
            padding: 80px 40px;
        }}
        
        .placeholder-title {{
            font-size: 72px;
            margin-bottom: 40px;
            text-shadow: 4px 4px 8px rgba(0,0,0,0.9);
            font-weight: 900;
        }}
        
        .placeholder-subtitle {{
            font-size: 42px;
            opacity: 0.8;
            margin-bottom: 40px;
            font-weight: bold;
        }}
        
        .placeholder-ready {{
            font-size: 32px;
            color: #00ff00;
            font-weight: bold;
            animation: readyBlink 2s infinite;
        }}
        
        @keyframes readyBlink {{
            0%, 50% {{ opacity: 1; }}
            51%, 100% {{ opacity: 0.5; }}
        }}
        
        .cta-banner {{
            position: absolute;
            bottom: 200px;
            left: 0;
            right: 0;
            background: rgba(255,107,107,0.9);
            padding: 20px;
            text-align: center;
            animation: ctaSlide 3s infinite;
        }}
        
        @keyframes ctaSlide {{
            0%, 80% {{ transform: translateY(0); }}
            90% {{ transform: translateY(-10px); }}
            100% {{ transform: translateY(0); }}
        }}
        
        .cta-text {{
            font-size: 36px;
            font-weight: 900;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
        }}
    </style>
</head>
<body>
    <div class="mobile-container">
        <div class="content-area">
            <div class="live-badge">🔴 LIVE</div>
            <div class="qr-corner">QR<br>CODE</div>
            
            <div id="videoContainer">
                <div class="placeholder-mobile">
                    <div class="placeholder-title">🤖 AI LIVE</div>
                    <div class="placeholder-subtitle">COMMERCE</div>
                    <div class="placeholder-ready">📱 READY FOR CAPTURE</div>
                </div>
            </div>
            
            <div class="product-overlay" id="productOverlay" style="display: none;">
                <div class="product-name" id="productName">PRODUCT NAME</div>
                <div class="product-price" id="productPrice">฿0</div>
                <div class="product-description" id="productDescription">Product description</div>
            </div>
            
            <div class="cta-banner" id="ctaBanner" style="display: none;">
                <div class="cta-text" id="ctaText">สั่งซื้อได้เลย!</div>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let contentRotationInterval = null;
        
        function connectWebSocket() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {{
                console.log('Mobile display WebSocket connected');
            }};
            
            ws.onmessage = function(event) {{
                try {{
                    const data = JSON.parse(event.data);
                    if (data.type === 'content_update') {{
                        updateMobileContent(data.content);
                    }}
                }} catch (error) {{
                    console.error('WebSocket message error:', error);
                }}
            }};
            
            ws.onclose = function() {{
                console.log('Mobile display WebSocket disconnected');
                setTimeout(connectWebSocket, 3000);
            }};
        }}
        
        function updateMobileContent(content) {{
            const videoContainer = document.getElementById('videoContainer');
            const productOverlay = document.getElementById('productOverlay');
            const ctaBanner = document.getElementById('ctaBanner');
            
            if (content.video_path) {{
                videoContainer.innerHTML = `
                    <video class="video-player" autoplay loop muted playsinline>
                        <source src="${{content.video_path}}" type="video/mp4">
                    </video>
                `;
            }} else {{
                videoContainer.innerHTML = `
                    <div class="placeholder-mobile">
                        <div class="placeholder-title">🎬 CONTENT</div>
                        <div class="placeholder-subtitle">${{(content.product_info?.name || 'AI LIVE').toUpperCase()}}</div>
                        <div class="placeholder-ready">📱 STREAMING NOW</div>
                    </div>
                `;
            }}
            
            if (content.product_info) {{
                document.getElementById('productName').textContent = (content.product_info.name || '').toUpperCase();
                document.getElementById('productPrice').textContent = content.product_info.price || '฿0';
                document.getElementById('productDescription').textContent = content.product_info.description || '';
                productOverlay.style.display = 'block';
                
                // Show CTA banner if available
                if (content.script_info?.call_to_action) {{
                    document.getElementById('ctaText').textContent = content.script_info.call_to_action.toUpperCase();
                    ctaBanner.style.display = 'block';
                }}
            }} else {{
                productOverlay.style.display = 'none';
                ctaBanner.style.display = 'none';
            }}
        }}
        
        async function fetchCurrentContent() {{
            try {{
                const response = await fetch('/api/current-content');
                const data = await response.json();
                if (data.success && data.content) {{
                    updateMobileContent(data.content);
                }}
            }} catch (error) {{
                console.error('Failed to fetch current content:', error);
            }}
        }}
        
        // Prevent mobile browser zoom/scroll
        document.addEventListener('touchstart', function(e) {{
            if (e.touches.length > 1) {{
                e.preventDefault();
            }}
        }}, {{ passive: false }});
        
        document.addEventListener('touchmove', function(e) {{
            e.preventDefault();
        }}, {{ passive: false }});
        
        // Initialize
        connectWebSocket();
        fetchCurrentContent();
        setInterval(fetchCurrentContent, 3000); // Faster refresh for mobile
        
        // Keep screen awake
        if ('wakeLock' in navigator) {{
            navigator.wakeLock.request('screen').catch(err => {{
                console.log('Wake lock failed:', err);
            }});
        }}
    </script>
</body>
</html>"""
    
    async def connect_websocket(self, websocket: WebSocket):
        """เชื่อมต่อ WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"📱 WebSocket connected. Active connections: {len(self.active_connections)}")
    
    async def disconnect_websocket(self, websocket: WebSocket):
        """ตัดการเชื่อมต่อ WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"📱 WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def broadcast_update(self, message: dict):
        """ส่งข้อความ update ไปยัง WebSocket connections ทั้งหมด"""
        
        if not self.active_connections:
            return
        
        message_json = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                print(f"❌ Failed to send WebSocket message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            if connection in self.active_connections:
                self.active_connections.remove(connection)
    
    async def update_content(self, content_data: dict) -> Dict[str, Any]:
        """อัพเดทเนื้อหาที่แสดง"""
        
        try:
            print(f"🔄 Updating display content: {content_data}")
            
            # Update current content
            if "video_path" in content_data:
                self.current_content["video_path"] = content_data["video_path"]
            
            if "product_info" in content_data:
                self.current_content["product_info"] = content_data["product_info"]
            
            if "script_info" in content_data:
                self.current_content["script_info"] = content_data["script_info"]
            
            if "display_mode" in content_data:
                self.current_content["display_mode"] = content_data["display_mode"]
            
            self.current_content["updated_at"] = datetime.utcnow().isoformat()
            
            # Broadcast to WebSocket connections
            await self.broadcast_update({
                "type": "content_update",
                "content": self.current_content,
                "timestamp": self.current_content["updated_at"]
            })
            
            return {
                "success": True,
                "message": "Content updated successfully",
                "content": self.current_content,
                "active_connections": len(self.active_connections)
            }
            
        except Exception as e:
            print(f"❌ Failed to update content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_video_content(self, video_path: str, product_info: dict = None) -> Dict[str, Any]:
        """อัพเดทวิดีโอที่แสดง (integration กับ ai_video_service)"""
        
        try:
            # ตรวจสอบไฟล์วิดีโอ
            if video_path and not video_path.startswith('/'):
                # Convert to web path
                video_filename = Path(video_path).name
                web_video_path = f"/videos/{video_filename}"
            else:
                web_video_path = video_path
            
            content_update = {
                "video_path": web_video_path,
                "product_info": product_info or self.current_content.get("product_info"),
                "display_mode": "video"
            }
            
            result = await self.update_content(content_update)
            
            if result["success"]:
                print(f"✅ Video content updated: {web_video_path}")
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to update video content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_display_server(self) -> Dict[str, Any]:
        """หยุด display server"""
        
        try:
            if self.server_process:
                self.server_process.should_exit = True
                self.is_running = False
                
                # Close all WebSocket connections
                for connection in self.active_connections:
                    try:
                        await connection.close()
                    except:
                        pass
                
                self.active_connections.clear()
                
                return {
                    "success": True,
                    "message": "Display server stopped successfully"
                }
            else:
                return {
                    "success": True,
                    "message": "Display server was not running"
                }
                
        except Exception as e:
            print(f"❌ Failed to stop display server: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_port_in_use(self, port: int) -> bool:
        """ตรวจสอบว่า port ถูกใช้งานอยู่หรือไม่"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def get_service_status(self) -> Dict[str, Any]:
        """ตรวจสอบสถานะของ service"""
        
        return {
            "service_name": "Content Display Service",
            "version": "1.0.0",
            "status": "active",
            "server_running": self.is_running,
            "server_url": f"http://localhost:{self.display_config['port']}" if self.is_running else None,
            "active_connections": len(self.active_connections),
            "current_content": self.current_content,
            "display_config": self.display_config,
            "directories": {
                "display_pages": str(self.display_dir),
                "static_files": str(self.static_dir),
                "video_source": str(self.video_dir)
            },
            "features": [
                "Real-time WebSocket updates",
                "9:16 aspect ratio (TikTok optimized)",
                "Multiple display modes (main, fullscreen, mobile)",
                "High contrast mobile display",
                "Auto-refresh fallback",
                "Video content integration",
                "Product information overlay"
            ]
        }

# Global service instance
content_display_service = ContentDisplayService()

print("🖥️ Content Display Service loaded")
print("🚀 Ready to start display server for mobile capture")