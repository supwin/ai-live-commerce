# app/services/avatar_service.py - แทนที่ไฟล์เดิมทั้งหมด

"""
Live2D Avatar Service with Working Speech Queue
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

# Import TTS service
try:
    from app.services.tts_service import tts_service
    print("✅ TTS service imported")
except ImportError as e:
    print(f"⚠️ TTS service import failed: {e}")
    tts_service = None

class SpeechPriority(Enum):
    """Speech priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

@dataclass
class SpeechRequest:
    """Speech request with priority and metadata"""
    text: str
    priority: SpeechPriority = SpeechPriority.NORMAL
    audio_url: Optional[str] = None
    duration: float = 2.0
    emotion: Optional[str] = None
    gesture: Optional[str] = None
    can_interrupt: bool = False
    source: str = "system"
    timestamp: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: f"speech_{int(time.time())}_{hash(time.time()) % 10000}")

class SpeechQueue:
    """Speech queue with priority management"""
    
    def __init__(self):
        self.queue: List[SpeechRequest] = []
        self.current_speech: Optional[SpeechRequest] = None
        self.is_processing = False
        self.is_paused = False
        self._lock = asyncio.Lock()
        print("🎙️ Speech Queue initialized")
    
    async def add_speech(self, request: SpeechRequest) -> bool:
        """Add speech request to queue with priority handling"""
        async with self._lock:
            # Handle interruption for urgent priority
            if (request.priority == SpeechPriority.URGENT and 
                self.current_speech and 
                request.can_interrupt):
                
                print(f"🔥 Interrupting current speech for urgent: {request.text[:50]}...")
                # Stop current speech and insert at front
                self.is_processing = False
                self.queue.insert(0, request)
                return True
            
            # Add to queue based on priority
            inserted = False
            for i, queued in enumerate(self.queue):
                if request.priority.value > queued.priority.value:
                    self.queue.insert(i, request)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(request)
            
            print(f"➕ Added to speech queue [{request.priority.name}]: {request.text[:50]}... (Queue: {len(self.queue)})")
            return True
    
    async def get_next_speech(self) -> Optional[SpeechRequest]:
        """Get next speech request from queue"""
        async with self._lock:
            if self.queue and not self.is_paused:
                return self.queue.pop(0)
            return None
    
    async def clear_queue(self, keep_high_priority: bool = True):
        """Clear speech queue"""
        async with self._lock:
            if keep_high_priority:
                self.queue = [req for req in self.queue 
                             if req.priority.value >= SpeechPriority.HIGH.value]
                print(f"🧹 Cleared low priority speeches, kept {len(self.queue)} high priority")
            else:
                self.queue.clear()
                print("🧹 Cleared all speech queue")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "queue_length": len(self.queue),
            "is_processing": self.is_processing,
            "is_paused": self.is_paused,
            "current_speech": self.current_speech.text[:50] if self.current_speech else None,
            "queue_items": [
                {
                    "text": req.text[:30] + "..." if len(req.text) > 30 else req.text,
                    "priority": req.priority.name,
                    "source": req.source,
                    "id": req.id,
                    "timestamp": req.timestamp,
                    "duration": req.duration
                }
                for req in self.queue[:10]  # Show first 10
            ]
        }

class AvatarEmotion(Enum):
    """Avatar emotion states"""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    THINKING = "thinking"
    EXCITED = "excited"
    LOVE = "love"
    WINK = "wink"

class AvatarGesture(Enum):
    """Avatar gesture animations"""
    IDLE = "idle"
    WAVE = "wave"
    POINT = "point"
    THUMBS_UP = "thumbs_up"
    CLAP = "clap"
    BOW = "bow"
    PRESENT = "present"
    THINK = "think"

class Live2DAvatarController:
    """Main controller for Live2D Avatar with Working Speech Queue"""
    
    def __init__(self):
        self.speech_queue = SpeechQueue()
        self.is_initialized = False
        self.websocket_clients = set()
        self.current_emotion = AvatarEmotion.NEUTRAL
        self.current_gesture = AvatarGesture.IDLE
        
        # Speech processing
        self._speech_task = None
        self._is_running = False
        
        print("🎭 Avatar Controller initialized with Speech Queue")
    
    async def initialize(self, model_path: str = "models/hiyori"):
        """Initialize Live2D model"""
        self.model_path = model_path
        self.is_initialized = True
        
        # Start speech processing task
        if not self._speech_task or self._speech_task.done():
            self._is_running = True
            self._speech_task = asyncio.create_task(self._process_speech_queue())
        
        print(f"✅ Live2D Avatar initialized: {model_path}")
        return True
    
    async def speak(
        self, 
        text: str, 
        priority: SpeechPriority = SpeechPriority.NORMAL,
        audio_url: Optional[str] = None, 
        duration: float = None,
        can_interrupt: bool = False,
        source: str = "api"
    ):
        """Add speech to queue (main entry point)"""
        if not self.is_initialized:
            await self.initialize()
        
        # Calculate duration based on text length if not provided
        if duration is None:
            duration = max(2.0, len(text) * 0.05 + 1.0)  # ~50ms per character + 1s base
        
        # Create speech request
        request = SpeechRequest(
            text=text,
            priority=priority,
            audio_url=audio_url,
            duration=duration,
            can_interrupt=can_interrupt,
            source=source
        )
        
        # Add to queue
        await self.speech_queue.add_speech(request)
        
        print(f"🗣️ Queued speech [{priority.name}]: {text[:30]}... (Duration: {duration:.1f}s)")
        
        return True
    
    async def speak_immediately(
        self, 
        text: str, 
        audio_url: Optional[str] = None, 
        duration: float = None
    ):
        """Speak immediately (interrupting current speech)"""
        if duration is None:
            duration = max(2.0, len(text) * 0.05 + 1.0)
            
        return await self.speak(
            text=text,
            priority=SpeechPriority.URGENT,
            audio_url=audio_url,
            duration=duration,
            can_interrupt=True,
            source="interrupt"
        )
    
    async def respond_to_chat(self, text: str, duration: float = None):
        """Respond to chat with higher priority"""
        if duration is None:
            duration = max(2.0, len(text) * 0.05 + 1.0)
            
        return await self.speak(
            text=text,
            priority=SpeechPriority.HIGH,
            duration=duration,
            can_interrupt=False,
            source="chat"
        )
    
    async def _process_speech_queue(self):
        """Main speech processing loop"""
        print("🎙️ Speech queue processor started")
        
        while self._is_running:
            try:
                # Check if we should process next speech
                if not self.speech_queue.is_processing and not self.speech_queue.is_paused:
                    next_speech = await self.speech_queue.get_next_speech()
                    
                    if next_speech:
                        await self._execute_speech(next_speech)
                
                await asyncio.sleep(0.1)  # Small delay to prevent busy loop
                
            except Exception as e:
                print(f"❌ Speech queue processing error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_speech(self, request: SpeechRequest):
        """Execute a speech request"""
        try:
            print(f"🗣️ Executing speech [{request.priority.name}]: {request.text[:50]}...")
            
            # Set processing state
            self.speech_queue.is_processing = True
            self.speech_queue.current_speech = request
            
            # Generate TTS if no audio URL provided
            if not request.audio_url and tts_service:
                temp_id = hashlib.md5(request.text.encode()).hexdigest()[:8]
                _, audio_url = await tts_service.generate_speech(request.text, temp_id)
                request.audio_url = audio_url
            
            # Send to WebSocket clients (Avatar page)
            message = {
                "type": "speak",
                "text": request.text,
                "audio_url": request.audio_url,
                "duration": request.duration,
                "priority": request.priority.name,
                "source": request.source,
                "emotion": request.emotion or "neutral",
                "timestamp": time.time()
            }
            
            await self._broadcast_to_clients(message)
            
            # Wait for speech to complete
            print(f"⏱️ Speaking for {request.duration:.1f} seconds...")
            await asyncio.sleep(request.duration)
            
            # Clean up
            self.speech_queue.is_processing = False
            self.speech_queue.current_speech = None
            
            print(f"✅ Completed speech: {request.text[:30]}...")
            
        except Exception as e:
            print(f"❌ Speech execution error: {e}")
            self.speech_queue.is_processing = False
            self.speech_queue.current_speech = None
    
    async def _stop_current_speech(self):
        """Stop current speech"""
        if self.speech_queue.is_processing:
            message = {"type": "stop_speech"}
            await self._broadcast_to_clients(message)
            
            self.speech_queue.is_processing = False
            self.speech_queue.current_speech = None
            print("⏹️ Stopped current speech")
    
    async def clear_speech_queue(self, keep_high_priority: bool = True):
        """Clear speech queue"""
        await self.speech_queue.clear_queue(keep_high_priority)
    
    async def pause_queue(self):
        """Pause speech queue processing"""
        self.speech_queue.is_paused = True
        print("⏸️ Speech queue paused")
    
    async def resume_queue(self):
        """Resume speech queue processing"""
        self.speech_queue.is_paused = False
        print("▶️ Speech queue resumed")
    
    async def set_emotion(self, emotion: AvatarEmotion):
        """Set avatar emotion"""
        self.current_emotion = emotion
        
        message = {
            "type": "emotion",
            "emotion": emotion.value
        }
        
        await self._broadcast_to_clients(message)
    
    async def perform_gesture(self, gesture: AvatarGesture, duration: float = 2.0):
        """Perform a gesture animation"""
        self.current_gesture = gesture
        
        message = {
            "type": "gesture",
            "gesture": gesture.value,
            "duration": duration
        }
        
        await self._broadcast_to_clients(message)
        
        await asyncio.sleep(duration)
        self.current_gesture = AvatarGesture.IDLE
    
    async def _broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast message to all connected WebSocket clients"""
        if self.websocket_clients:
            message_json = json.dumps(message)
            disconnected = set()
            
            for client in self.websocket_clients.copy():
                try:
                    await client.send_text(message_json)
                except Exception as e:
                    print(f"⚠️ WebSocket client disconnected: {e}")
                    disconnected.add(client)
            
            # Remove disconnected clients
            self.websocket_clients -= disconnected
    
    def add_websocket_client(self, client):
        """Add WebSocket client for real-time updates"""
        self.websocket_clients.add(client)
        print(f"📡 Added WebSocket client. Total clients: {len(self.websocket_clients)}")
    
    def remove_websocket_client(self, client):
        """Remove WebSocket client"""
        self.websocket_clients.discard(client)
        print(f"📡 Removed WebSocket client. Total clients: {len(self.websocket_clients)}")
    
    def get_state(self) -> Dict[str, Any]:
        """Get current avatar state"""
        return {
            "emotion": self.current_emotion.value,
            "gesture": self.current_gesture.value,
            "is_speaking": self.speech_queue.is_processing,
            "is_initialized": self.is_initialized,
            "websocket_clients": len(self.websocket_clients),
            "speech_queue": self.speech_queue.get_queue_status()
        }
    
    async def shutdown(self):
        """Shutdown avatar controller"""
        self._is_running = False
        if self._speech_task:
            self._speech_task.cancel()
        print("🛑 Avatar Controller shutdown")

# Global avatar instance
avatar_controller = Live2DAvatarController()

# Auto-initialize
try:
    import asyncio
    loop = asyncio.get_event_loop()
    if not loop.is_running():
        asyncio.run(avatar_controller.initialize())
    else:
        # If loop is already running, schedule initialization
        loop.create_task(avatar_controller.initialize())
except Exception as e:
    print(f"Warning: Could not auto-initialize avatar: {e}")
    # Will initialize on first use