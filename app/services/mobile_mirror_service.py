"""
Mobile Screen Mirroring Service for TikTok Live
Handles screen mirroring and content display for mobile TikTok live streaming
"""

import asyncio
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import psutil
import socket

from app.core.config import get_settings
from app.core.logging import logger

class MobileMirrorService:
    def __init__(self):
        self.settings = get_settings()
        self.mirror_process = None
        self.is_mirroring = False
        self.device_connected = False
        self.current_content = None
        
        # Mirror configuration
        self.mirror_method = "scrcpy"  # Default to scrcpy (Android)
        self.device_ip = None
        self.device_port = 5555
        self.mirror_quality = "medium"
        
        # Content display settings
        self.content_window_size = (1080, 1920)  # 9:16 for TikTok
        self.content_display_port = 8080
        self.web_display_process = None
        
    async def detect_devices(self) -> Dict:
        """
        Detect connected mobile devices (Android/iOS)
        
        Returns:
            Information about connected devices
        """
        devices = {
            "android_devices": [],
            "ios_devices": [],
            "total_count": 0
        }
        
        try:
            # Check for Android devices via ADB
            android_devices = await self._check_android_devices()
            devices["android_devices"] = android_devices
            
            # Check for iOS devices (basic detection)
            ios_devices = await self._check_ios_devices()
            devices["ios_devices"] = ios_devices
            
            devices["total_count"] = len(android_devices) + len(ios_devices)
            
            print("INFO: "f"Detected {devices['total_count']} mobile devices")
            
            return {
                "success": True,
                "devices": devices,
                "recommendations": self._get_device_recommendations(devices)
            }
            
        except Exception as e:
            print("ERROR: "f"Device detection failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "devices": devices
            }
    
    async def _check_android_devices(self) -> List[Dict]:
        """Check for connected Android devices via ADB"""
        devices = []
        
        try:
            # Run adb devices command
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    if line.strip() and 'device' in line:
                        parts = line.split()
                        device_id = parts[0]
                        status = parts[1] if len(parts) > 1 else "unknown"
                        
                        # Get device info
                        device_info = await self._get_android_device_info(device_id)
                        device_info.update({
                            "device_id": device_id,
                            "status": status,
                            "platform": "android"
                        })
                        
                        devices.append(device_info)
            
        except FileNotFoundError:
            print("WARNING: ""ADB not found - Android device detection unavailable")
        except subprocess.TimeoutExpired:
            print("WARNING: ""ADB command timed out")
        except Exception as e:
            print("ERROR: "f"Android device check failed: {str(e)}")
        
        return devices
    
    async def _get_android_device_info(self, device_id: str) -> Dict:
        """Get detailed information about Android device"""
        device_info = {
            "model": "Unknown",
            "version": "Unknown",
            "resolution": "Unknown",
            "battery": "Unknown"
        }
        
        try:
            # Get device model
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                device_info["model"] = result.stdout.strip()
            
            # Get Android version
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "getprop", "ro.build.version.release"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                device_info["version"] = f"Android {result.stdout.strip()}"
            
            # Get screen resolution
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "wm", "size"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                resolution_line = result.stdout.strip()
                if "Physical size:" in resolution_line:
                    device_info["resolution"] = resolution_line.split("Physical size: ")[1]
            
        except Exception as e:
            print("WARNING: "f"Could not get detailed info for device {device_id}: {str(e)}")
        
        return device_info
    
    async def _check_ios_devices(self) -> List[Dict]:
        """Check for connected iOS devices (basic detection)"""
        devices = []
        
        try:
            # Check if iOS device detection tools are available
            # This is a simplified check - full iOS support requires additional tools
            result = subprocess.run(
                ["system_profiler", "SPUSBDataType"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "iPhone" in result.stdout:
                devices.append({
                    "device_id": "ios_device_detected",
                    "model": "iPhone (detected)",
                    "platform": "ios",
                    "status": "connected",
                    "note": "iOS mirroring requires additional setup"
                })
            
        except FileNotFoundError:
            # system_profiler not available (not macOS)
            pass
        except Exception as e:
            print("WARNING: "f"iOS device detection failed: {str(e)}")
        
        return devices
    
    def _get_device_recommendations(self, devices: Dict) -> List[str]:
        """Get recommendations based on detected devices"""
        recommendations = []
        
        if devices["total_count"] == 0:
            recommendations.extend([
                "No devices detected. Please connect your mobile device via USB",
                "For Android: Enable USB Debugging in Developer Options",
                "For iOS: Consider using wireless mirroring or third-party tools"
            ])
        
        if devices["android_devices"]:
            recommendations.extend([
                "Android device detected - scrcpy is recommended for best performance",
                "Ensure USB Debugging is enabled",
                "Consider using wireless connection for better mobility"
            ])
        
        if devices["ios_devices"]:
            recommendations.extend([
                "iOS device detected - consider using AirPlay or QuickTime Player",
                "Third-party solutions like Reflector or LonelyScreen may be needed"
            ])
        
        return recommendations
    
    async def setup_android_mirroring(self, device_id: str = None, wireless: bool = False) -> Dict:
        """
        Setup Android screen mirroring using scrcpy
        
        Args:
            device_id: Specific device ID (optional)
            wireless: Use wireless connection
            
        Returns:
            Setup status and information
        """
        try:
            # Install/check scrcpy
            scrcpy_available = await self._check_scrcpy_installation()
            if not scrcpy_available:
                return {
                    "success": False,
                    "error": "scrcpy not installed",
                    "installation_guide": await self._get_scrcpy_installation_guide()
                }
            
            # Setup wireless connection if requested
            if wireless and device_id:
                wireless_setup = await self._setup_wireless_connection(device_id)
                if not wireless_setup["success"]:
                    return wireless_setup
            
            # Prepare scrcpy command
            scrcpy_cmd = self._build_scrcpy_command(device_id, wireless)
            
            return {
                "success": True,
                "message": "Android mirroring setup completed",
                "command": " ".join(scrcpy_cmd),
                "device_id": device_id,
                "wireless": wireless,
                "next_steps": [
                    "Start mirroring with start_mirroring()",
                    "Open TikTok app on your phone", 
                    "Start content display server",
                    "Begin live streaming"
                ]
            }
            
        except Exception as e:
            print("ERROR: "f"Android mirroring setup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _check_scrcpy_installation(self) -> bool:
        """Check if scrcpy is installed and available"""
        try:
            result = subprocess.run(
                ["scrcpy", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    async def _get_scrcpy_installation_guide(self) -> Dict:
        """Get installation guide for scrcpy"""
        return {
            "windows": [
                "Download from: https://github.com/Genymobile/scrcpy/releases",
                "Extract to a folder and add to PATH",
                "Or install via: winget install scrcpy"
            ],
            "macos": [
                "Install via Homebrew: brew install scrcpy",
                "Or download from GitHub releases"
            ],
            "linux": [
                "Ubuntu/Debian: sudo apt install scrcpy",
                "Arch: sudo pacman -S scrcpy",
                "Or compile from source"
            ],
            "requirements": [
                "Android device with Android 5.0+",
                "USB Debugging enabled",
                "ADB installed and working"
            ]
        }
    
    async def _setup_wireless_connection(self, device_id: str) -> Dict:
        """Setup wireless ADB connection for Android device"""
        try:
            # Get device IP address
            result = subprocess.run(
                ["adb", "-s", device_id, "shell", "ip", "route"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": "Could not get device IP address"
                }
            
            # Parse IP address (simplified)
            lines = result.stdout.strip().split('\n')
            device_ip = None
            for line in lines:
                if "wlan0" in line and "src" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "src" and i + 1 < len(parts):
                            device_ip = parts[i + 1]
                            break
                    if device_ip:
                        break
            
            if not device_ip:
                return {
                    "success": False,
                    "error": "Could not determine device IP address"
                }
            
            # Enable TCP/IP mode
            subprocess.run(
                ["adb", "-s", device_id, "tcpip", "5555"],
                capture_output=True,
                timeout=10
            )
            
            # Wait a moment for the change to take effect
            await asyncio.sleep(2)
            
            # Connect to device wirelessly
            result = subprocess.run(
                ["adb", "connect", f"{device_ip}:5555"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and "connected" in result.stdout:
                self.device_ip = device_ip
                return {
                    "success": True,
                    "device_ip": device_ip,
                    "message": f"Wireless connection established to {device_ip}:5555"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to connect wirelessly: {result.stdout}"
                }
                
        except Exception as e:
            print("ERROR: "f"Wireless setup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_scrcpy_command(self, device_id: str = None, wireless: bool = False) -> List[str]:
        """Build scrcpy command with appropriate parameters"""
        cmd = ["scrcpy"]
        
        # Device selection
        if device_id:
            if wireless and self.device_ip:
                cmd.extend(["-s", f"{self.device_ip}:5555"])
            else:
                cmd.extend(["-s", device_id])
        
        # Quality settings
        quality_settings = {
            "low": ["--bit-rate", "2M", "--max-size", "800"],
            "medium": ["--bit-rate", "4M", "--max-size", "1080"],
            "high": ["--bit-rate", "8M", "--max-size", "1920"]
        }
        
        cmd.extend(quality_settings.get(self.mirror_quality, quality_settings["medium"]))
        
        # Additional optimizations
        cmd.extend([
            "--always-on-top",        # Keep mirror window on top
            "--turn-screen-off",      # Turn off device screen to save battery
            "--stay-awake",           # Keep device awake
            "--disable-screensaver"   # Disable screensaver
        ])
        
        return cmd
    
    async def start_mirroring(self, device_id: str = None) -> Dict:
        """
        Start screen mirroring
        
        Args:
            device_id: Device to mirror (optional)
            
        Returns:
            Mirroring status
        """
        try:
            if self.is_mirroring:
                return {
                    "success": False,
                    "message": "Mirroring already active",
                    "current_device": device_id
                }
            
            # Build and execute scrcpy command
            scrcpy_cmd = self._build_scrcpy_command(device_id, bool(self.device_ip))
            
            # Start mirroring process
            self.mirror_process = subprocess.Popen(
                scrcpy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment to check if process started successfully
            await asyncio.sleep(2)
            
            if self.mirror_process.poll() is None:
                # Process is running
                self.is_mirroring = True
                self.device_connected = True
                
                print("INFO: "f"Screen mirroring started for device: {device_id}")
                
                return {
                    "success": True,
                    "message": "Screen mirroring started successfully",
                    "device_id": device_id,
                    "process_id": self.mirror_process.pid,
                    "instructions": [
                        "Mirror window should now be visible",
                        "Open TikTok app on your phone",
                        "Start content display server",
                        "Position AI content in view of phone camera"
                    ]
                }
            else:
                # Process failed to start
                error_output = self.mirror_process.stderr.read().decode()
                return {
                    "success": False,
                    "message": "Failed to start mirroring",
                    "error": error_output
                }
                
        except Exception as e:
            print("ERROR: "f"Failed to start mirroring: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def stop_mirroring(self) -> Dict:
        """
        Stop screen mirroring
        
        Returns:
            Stop status
        """
        try:
            if not self.is_mirroring or not self.mirror_process:
                return {
                    "success": True,
                    "message": "No active mirroring to stop"
                }
            
            # Terminate mirroring process
            self.mirror_process.terminate()
            
            # Wait for process to end
            try:
                self.mirror_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if not terminated gracefully
                self.mirror_process.kill()
                self.mirror_process.wait()
            
            self.is_mirroring = False
            self.device_connected = False
            self.mirror_process = None
            
            print("INFO: ""Screen mirroring stopped")
            
            return {
                "success": True,
                "message": "Screen mirroring stopped successfully",
                "stopped_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print("ERROR: "f"Failed to stop mirroring: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start_content_display_server(self) -> Dict:
        """
        Start web server to display AI-generated content
        
        Returns:
            Server status
        """
        try:
            # Check if port is available
            if self._is_port_in_use(self.content_display_port):
                return {
                    "success": False,
                    "error": f"Port {self.content_display_port} is already in use"
                }
            
            # Create content display HTML
            display_html = self._create_content_display_html()
            
            # Save HTML file
            display_file = Path("frontend/mobile_display/index.html")
            display_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(display_file, 'w', encoding='utf-8') as f:
                f.write(display_html)
            
            # Start simple HTTP server
            server_cmd = [
                "python", "-m", "http.server", 
                str(self.content_display_port),
                "--directory", "frontend/mobile_display"
            ]
            
            self.web_display_process = subprocess.Popen(
                server_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment to ensure server starts
            await asyncio.sleep(1)
            
            if self.web_display_process.poll() is None:
                return {
                    "success": True,
                    "message": "Content display server started",
                    "url": f"http://localhost:{self.content_display_port}",
                    "port": self.content_display_port,
                    "instructions": [
                        f"Open http://localhost:{self.content_display_port} in browser",
                        "Point your phone camera at the browser window",
                        "Content will update automatically from AI service"
                    ]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to start content display server"
                }
                
        except Exception as e:
            print("ERROR: "f"Failed to start content display server: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is already in use"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except OSError:
                return True
    
    def _create_content_display_html(self) -> str:
        """Create HTML for content display"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AI Live Commerce - Mobile Display</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #000;
            font-family: Arial, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            color: white;
        }}
        
        .video-container {{
            width: 90vw;
            max-width: 600px;
            position: relative;
        }}
        
        .video-player {{
            width: 100%;
            height: auto;
            border-radius: 10px;
        }}
        
        .overlay {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            padding: 15px;
            border-radius: 8px;
            backdrop-filter: blur(10px);
        }}
        
        .product-name {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .product-price {{
            font-size: 20px;
            color: #ff6b6b;
            margin-bottom: 5px;
        }}
        
        .product-description {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .live-indicator {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: #ff0000;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
            100% {{ opacity: 1; }}
        }}
        
        .status-message {{
            text-align: center;
            font-size: 18px;
            opacity: 0.8;
            margin-top: 20px;
        }}
        
        .qr-code {{
            margin-top: 20px;
            text-align: center;
        }}
        
        .qr-code img {{
            width: 150px;
            height: 150px;
            background: white;
            padding: 10px;
            border-radius: 8px;
        }}
    </style>
</head>
<body>
    <div class="video-container">
        <div class="live-indicator">🔴 LIVE</div>
        
        <video id="ai-video" class="video-player" autoplay loop muted>
            <source src="/videos/current.mp4" type="video/mp4">
            Your browser does not support the video tag.
        </video>
        
        <div class="overlay">
            <div class="product-name" id="product-name">AI Live Commerce</div>
            <div class="product-price" id="product-price">Starting Soon...</div>
            <div class="product-description" id="product-description">
                Intelligent product demonstrations powered by AI
            </div>
        </div>
    </div>
    
    <div class="status-message">
        Point your phone camera at this screen for TikTok Live
    </div>
    
    <div class="qr-code">
        <div style="color: #666; margin-bottom: 10px;">Quick Access QR Code</div>
        <div style="width: 150px; height: 150px; background: white; margin: 0 auto; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: black;">
            QR Code Here
        </div>
    </div>
    
    <script>
        let currentVideo = null;
        let updateInterval = null;
        
        async function updateContent() {{
            try {{
                const response = await fetch('/api/v1/mobile-live/current-content');
                const data = await response.json();
                
                if (data.success) {{
                    // Update video source if changed
                    if (data.video_path && data.video_path !== currentVideo) {{
                        const video = document.getElementById('ai-video');
                        video.src = data.video_path;
                        currentVideo = data.video_path;
                    }}
                    
                    // Update product information
                    if (data.product_info) {{
                        document.getElementById('product-name').textContent = 
                            data.product_info.name || 'AI Live Commerce';
                        document.getElementById('product-price').textContent = 
                            data.product_info.price || 'Special Offer';
                        document.getElementById('product-description').textContent = 
                            data.product_info.description || 'Powered by AI';
                    }}
                }}
            }} catch (error) {{
                console.log('Content update failed:', error);
            }}
        }}
        
        // Update content every 5 seconds
        updateInterval = setInterval(updateContent, 5000);
        
        // Initial content load
        updateContent();
        
        // Handle video errors gracefully
        document.getElementById('ai-video').addEventListener('error', function() {{
            console.log('Video load error - will retry');
            setTimeout(updateContent, 2000);
        }});
    </script>
</body>
</html>
        """
    
    async def update_display_content(self, video_path: str = None, product_info: dict = None) -> Dict:
        """
        Update content being displayed for mobile capture
        
        Args:
            video_path: Path to new video content
            product_info: Product information to display
            
        Returns:
            Update status
        """
        try:
            self.current_content = {
                "video_path": video_path,
                "product_info": product_info,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # If video path provided, copy to display location
            if video_path and Path(video_path).exists():
                display_video_path = Path("frontend/mobile_display/videos/current.mp4")
                display_video_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy video file
                import shutil
                shutil.copy2(video_path, display_video_path)
            
            return {
                "success": True,
                "message": "Display content updated",
                "content": self.current_content
            }
            
        except Exception as e:
            print("ERROR: "f"Failed to update display content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_mirror_status(self) -> Dict:
        """
        Get current mirroring status
        
        Returns:
            Current status information
        """
        return {
            "is_mirroring": self.is_mirroring,
            "device_connected": self.device_connected,
            "device_ip": self.device_ip,
            "mirror_method": self.mirror_method,
            "mirror_quality": self.mirror_quality,
            "content_server_running": self.web_display_process is not None and self.web_display_process.poll() is None,
            "content_server_url": f"http://localhost:{self.content_display_port}" if self.web_display_process else None,
            "current_content": self.current_content
        }

# Create global instance
mobile_mirror_service = MobileMirrorService()