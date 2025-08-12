# app/services/integration_hub.py (Updated for Speech Queue)
"""
Integration Hub - เชื่อมต่อ AI, Avatar, และ Live Platforms
Updated with Speech Queue management
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import services with error handling
try:
    from app.services.avatar_service import avatar_controller, SpeechPriority
    print("✅ Avatar service with Speech Queue imported")
except ImportError as e:
    print(f"⚠️ Avatar service import failed: {e}")
    avatar_controller = None
    SpeechPriority = None

try:
    from app.services.tts_service import tts_service
    print("✅ TTS service imported")
except ImportError as e:
    print(f"⚠️ TTS service import failed: {e}")
    tts_service = None

try:
    from app.services.ai_script_service import ai_script_service
    print("✅ AI script service imported")
except ImportError as e:
    print(f"⚠️ AI script service import failed: {e}")
    ai_script_service = None

try:
    from app.services.facebook_live_service import facebook_service
    print("✅ Facebook service imported")
except ImportError as e:
    print(f"⚠️ Facebook service import failed: {e}")
    facebook_service = None


class LiveCommerceOrchestrator:
    """Central orchestrator for AI Live Commerce system with Speech Queue"""
    
    def __init__(self):
        self.is_active = False
        self.current_platform = None
        self.auto_response_enabled = True
        self.current_product = None
        self.presentation_queue = []
        self.comment_processors = []
        
        # Service references
        self.avatar_controller = avatar_controller
        self.tts_service = tts_service
        self.ai_script_service = ai_script_service
        self.facebook_service = facebook_service
        
        # Analytics
        self.session_stats = {
            "start_time": None,
            "comments_processed": 0,
            "auto_responses_sent": 0,
            "products_presented": 0,
            "viewers_peak": 0,
            "speeches_queued": 0,
            "speeches_completed": 0
        }
        
        # AI Response templates for different scenarios
        self.response_templates = {
            "greeting": [
                "สวัสดีครับ! ยินดีต้อนรับสู่ไลฟ์ขายของ 🙏",
                "เฮ้ย! สวัสดีครับ ขอบคุณที่เข้ามาดูนะครับ 😊",
                "ยินดีต้อนรับครับ! วันนี้มีของดีๆ มาแนะนำเยอะเลย"
            ],
            "price_inquiry": [
                "ราคาจะแสดงในคอมเมนต์ครับ รอสักครู่นะครับ 💰",
                "ขอบคุณที่สนใจครับ ราคาพิเศษจะประกาศให้ฟังเลยครับ",
                "ราคาดีมากครับ รับรองคุ้มค่าแน่นอน ติดตามต่อนะครับ"
            ],
            "interest": [
                "ขอบคุณที่สนใจครับ! รายละเอียดจะบอกให้ฟังทันทีเลยครับ 🎉",
                "เยี่ยมเลยครับ! คนที่สนใจแบบนี้แหละที่เราชอบ",
                "สนใจดีครับ! รอดูข้อมูลเพิ่มเติมนะครับ"
            ],
            "question": [
                "คำถามดีครับ! ขอตอบให้ฟังทันทีเลยนะครับ",
                "ถามได้เลยครับ เราพร้อมตอบทุกคำถาม 😊",
                "ดีที่ถามครับ! รายละเอียดจะอธิบายให้ฟังเลย"
            ]
        }
        
        print("🎯 Integration Hub initialized with Speech Queue support")
    
    async def start_live_session(self, platform: str = "facebook", product_focus: str = None):
        """Start integrated live commerce session - UPDATED"""
        try:
            print(f"🚀 Starting live commerce session on {platform}")
            
            self.is_active = True
            self.current_platform = platform
            self.session_stats["start_time"] = datetime.now()
            
            # Initialize avatar if available
            if self.avatar_controller:
                try:
                    await self.avatar_controller.initialize()
                    # Clear any existing speech queue
                    await self.avatar_controller.clear_speech_queue(keep_high_priority=False)
                    print("✅ Avatar initialized and speech queue cleared")
                except Exception as e:
                    print(f"⚠️ Avatar initialization failed: {e}")
            
            # Start platform-specific live stream
            if platform == "facebook" and self.facebook_service:
                await self._start_facebook_integration()
            else:
                print(f"⚠️ Platform {platform} not available, using mock mode")
            
            # Start comment monitoring
            await self._start_comment_monitoring()
            
            # Welcome message with normal priority - THIS WILL NOW QUEUE PROPERLY
            welcome_text = "สวัสดีครับทุกคน! วันนี้เรามาขายของกันแบบสดๆ ร้อนๆ มี AI มาช่วยนำเสนอสินค้าด้วยนะครับ!"
            if SpeechPriority:
                await self.avatar_speak(welcome_text, priority=SpeechPriority.NORMAL, source="session_start")
            else:
                await self.avatar_speak(welcome_text, source="session_start")
            
            print("✅ Live commerce session started successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start live session: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _start_facebook_integration(self):
        """Start Facebook Live integration"""
        try:
            if not self.facebook_service.page_access_token:
                print("⚠️ Facebook not properly connected, using mock mode")
            
            if not self.facebook_service.live_video_id:
                await self.facebook_service.create_live_video(
                    title="AI Live Commerce - ขายสินค้าออนไลน์",
                    description="ขายสินค้าคุณภาพดี ราคาพิเศษ พร้อม AI Assistant นำเสนอ"
                )
                print("✅ Facebook Live video created")
                
        except Exception as e:
            print(f"⚠️ Facebook integration error: {e}")
    
    async def _start_comment_monitoring(self):
        """Start monitoring comments from all platforms"""
        try:
            asyncio.create_task(self._facebook_comment_monitor())
            print("✅ Comment monitoring started")
        except Exception as e:
            print(f"⚠️ Comment monitoring start error: {e}")
    
    async def _facebook_comment_monitor(self):
        """Monitor Facebook Live comments"""
        while self.is_active:
            try:
                if self.facebook_service and self.facebook_service.live_video_id:
                    comments = await self.facebook_service.get_live_comments(limit=5)
                    
                    for comment in comments:
                        await self._process_comment(comment, "facebook")
                
                await asyncio.sleep(3)
                
            except Exception as e:
                print(f"❌ Comment monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _process_comment(self, comment: Dict[str, Any], platform: str):
        """Process incoming comment with AI and proper priority - UPDATED"""
        try:
            user_name = comment.get("from", {}).get("name", "Unknown")
            message = comment.get("message", "")
            
            print(f"💬 Processing comment from {user_name}: {message}")
            
            # Update stats
            self.session_stats["comments_processed"] += 1
            
            # Analyze comment intent
            intent = await self._analyze_comment_intent(message)
            
            # Generate appropriate response
            if self.auto_response_enabled:
                response = await self._generate_response(message, intent, user_name)
                
                if response:
                    # Send response to platform
                    await self._send_platform_response(response, platform)
                    
                    # Make avatar speak with HIGH priority for chat responses
                    if intent in ["price_inquiry", "interest", "question"]:
                        if SpeechPriority:
                            await self.avatar_speak(
                                response, 
                                priority=SpeechPriority.HIGH,
                                source="chat_response"
                            )
                        else:
                            await self.avatar_speak(response, source="chat_response")
                    
                    self.session_stats["auto_responses_sent"] += 1
            
            # Trigger product presentation if relevant
            if intent == "interest" and self.current_product:
                await self._present_current_product()
            
        except Exception as e:
            print(f"❌ Comment processing error: {e}")
    
    async def _analyze_comment_intent(self, message: str) -> str:
        """Analyze comment intent using keywords"""
        message_lower = message.lower()
        
        # Price inquiries
        if any(keyword in message_lower for keyword in ['ราคา', 'เท่าไหร่', 'price', 'cost', 'บาท']):
            return "price_inquiry"
        
        # Interest indicators
        if any(keyword in message_lower for keyword in ['สนใจ', 'เอา', 'ขอ', 'สั่ง', 'ซื้อ', 'want', 'interested']):
            return "interest"
        
        # Questions
        if any(keyword in message_lower for keyword in ['?', 'ไหม', 'อะไร', 'ยังไง', 'what', 'how', 'why']):
            return "question"
        
        # Greetings
        if any(keyword in message_lower for keyword in ['สวัสดี', 'hello', 'hi', 'hey']):
            return "greeting"
        
        return "general"
    
    async def _generate_response(self, original_message: str, intent: str, user_name: str) -> Optional[str]:
        """Generate appropriate response"""
        try:
            templates = self.response_templates.get(intent, [])
            
            if templates:
                import random
                base_response = random.choice(templates)
                
                if user_name and user_name != "Unknown":
                    base_response = f"คุณ{user_name} {base_response}"
                
                return base_response
            
            return None
            
        except Exception as e:
            print(f"❌ Response generation error: {e}")
            return None
    
    async def _send_platform_response(self, message: str, platform: str):
        """Send response to the platform"""
        try:
            if platform == "facebook" and self.facebook_service:
                await self.facebook_service.post_comment(message)
                print(f"📱 Sent response to {platform}: {message}")
            else:
                print(f"📱 Mock response to {platform}: {message}")
            
        except Exception as e:
            print(f"❌ Platform response error: {e}")
    
    async def avatar_speak(
        self, 
        text: str, 
        priority: Optional[object] = None, 
        with_emotion: str = None,
        source: str = "system"
    ):
        """Make avatar speak with priority support - UPDATED VERSION"""
        try:
            # Set default priority
            if not priority and SpeechPriority:
                priority = SpeechPriority.NORMAL
            elif not priority:
                priority = 2  # Fallback
            
            if self.avatar_controller and hasattr(self.avatar_controller, 'speak'):
                # Use the working speech queue system
                await self.avatar_controller.speak(
                    text=text,
                    priority=priority,
                    source=source
                )
                self.session_stats["speeches_queued"] += 1
                print(f"🎙️ Speech queued via integration hub: {text[:30]}...")
            else:
                print(f"🗣️ Avatar would say [{source}]: {text}")
                
        except Exception as e:
            print(f"❌ Avatar speak error: {e}")
    
    async def present_product(self, product, use_saved_script: bool = True):
        """Present a product using AI-generated script with proper queue - UPDATED"""
        try:
            if not product:
                print("❌ No product provided")
                return
                
            self.current_product = product
            
            print(f"🛍️ Presenting product: {product.name}")
            
            # Generate or use existing script
            if use_saved_script and hasattr(product, 'scripts') and product.scripts:
                script_content = product.scripts[0].content
            else:
                script_content = f"ขอแนะนำ {product.name} ครับ {product.description} ในราคา {product.price:,.0f} บาท สินค้าคุณภาพดี ราคาพิเศษ!"
            
            # Add to speech queue with NORMAL priority
            if SpeechPriority:
                await self.avatar_speak(
                    script_content, 
                    priority=SpeechPriority.NORMAL,
                    source="product_presentation"
                )
            else:
                await self.avatar_speak(
                    script_content,
                    source="product_presentation"
                )
            
            # Send to platform
            if self.current_platform:
                await self._send_platform_response(script_content, self.current_platform)
            
            self.session_stats["products_presented"] += 1
            
        except Exception as e:
            print(f"❌ Product presentation error: {e}")
    
    async def _present_current_product(self):
        """Present the current product (triggered by interest)"""
        if self.current_product:
            await self.present_product(self.current_product, use_saved_script=True)
    
    async def set_auto_response(self, enabled: bool):
        """Enable/disable auto-response"""
        self.auto_response_enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"🤖 Auto-response {status}")
        
        # Announce the change
        announcement = f"ระบบตอบกลับอัตโนมัติ{status}แล้วครับ"
        await self.avatar_speak(
            announcement, 
            priority=SpeechPriority.NORMAL if SpeechPriority else 2,
            source="system_announcement"
        )
    
    async def run_full_demo(self):
        """Run full demonstration with proper speech queue - UPDATED"""
        try:
            print("🎭 Starting full demo with working speech queue management...")
            
            # Clear existing queue first
            if self.avatar_controller:
                await self.avatar_controller.clear_speech_queue(keep_high_priority=False)
                print("🧹 Cleared speech queue for demo")
            
            # Start session if not active
            if not self.is_active:
                await self.start_live_session("facebook")
                await asyncio.sleep(1)  # Wait for initialization
            
            # Demo script sequence with proper timing and priority
            demo_scripts = [
                {
                    "text": "สวัสดีครับทุกคน! วันนี้มีโปรโมชั่นพิเศษมาแนะนำ",
                    "priority": SpeechPriority.NORMAL if SpeechPriority else 2,
                    "source": "demo_intro"
                },
                {
                    "text": "เรามีสินค้าคุณภาพดี ราคาดี มาให้เลือกสรรค์",
                    "priority": SpeechPriority.NORMAL if SpeechPriority else 2,
                    "source": "demo_product_intro"
                },
                {
                    "text": "ใครสนใจสินค้าไหน พิมพ์ในแชทได้เลยนะครับ",
                    "priority": SpeechPriority.NORMAL if SpeechPriority else 2,
                    "source": "demo_interaction"
                }
            ]
            
            # Add demo scripts to queue with small delays
            for i, script in enumerate(demo_scripts):
                await self.avatar_speak(
                    script["text"],
                    priority=script["priority"],
                    source=script["source"]
                )
                
                # Small delay between queuing (not speaking)
                await asyncio.sleep(0.3)
            
            # Present a demo product after a delay
            await asyncio.sleep(1)
            demo_product = type('DemoProduct', (), {
                'id': 'demo_product_001',
                'name': 'Smart Device Pro',
                'price': 1999.0,
                'description': 'อุปกรณ์อัจฉริยะล้ำสมัย ใช้งานง่าย คุ้มค่าสุดๆ'
            })()
            
            await self.present_product(demo_product, use_saved_script=False)
            
            # Final message
            await asyncio.sleep(0.5)
            final_text = "นี่คือระบบ AI Live Commerce ที่ทำงานแบบอัตโนมัติครับ!"
            if SpeechPriority:
                await self.avatar_speak(
                    final_text,
                    priority=SpeechPriority.NORMAL,
                    source="demo_conclusion"
                )
            else:
                await self.avatar_speak(final_text, source="demo_conclusion")
            
            print("✅ Full demo queued successfully - speeches will play in order")
            return True
            
        except Exception as e:
            print(f"❌ Full demo error: {e}")
            return False
    
    async def stop_live_session(self):
        """Stop live commerce session"""
        try:
            self.is_active = False
            
            # Clear speech queue except high priority messages
            if self.avatar_controller:
                await self.avatar_controller.clear_speech_queue(keep_high_priority=True)
            
            # End platform streams
            if self.current_platform == "facebook" and self.facebook_service:
                await self.facebook_service.end_live_video()
            
            # Final message with high priority
            await self.avatar_speak(
                "ขอบคุณทุกคนที่ติดตามครับ! แล้วเจอกันใหม่ไลฟ์หน้านะครับ!",
                priority=SpeechPriority.HIGH if SpeechPriority else 3,
                source="session_end"
            )
            
            # Update final stats
            self.session_stats["speeches_completed"] = self.session_stats["speeches_queued"]
            
            # Print session stats
            duration = datetime.now() - self.session_stats["start_time"] if self.session_stats["start_time"] else None
            print("📊 Session Statistics:")
            print(f"   Duration: {duration}")
            print(f"   Comments processed: {self.session_stats['comments_processed']}")
            print(f"   Auto-responses sent: {self.session_stats['auto_responses_sent']}")
            print(f"   Products presented: {self.session_stats['products_presented']}")
            print(f"   Speeches queued: {self.session_stats['speeches_queued']}")
            
            print("✅ Live commerce session ended")
            
        except Exception as e:
            print(f"❌ Session stop error: {e}")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status including speech queue"""
        base_status = {
            "active": self.is_active,
            "platform": self.current_platform,
            "auto_response_enabled": self.auto_response_enabled,
            "current_product": self.current_product.name if self.current_product else None,
            "stats": self.session_stats
        }
        
        # Add speech queue status if available
        if self.avatar_controller and hasattr(self.avatar_controller, 'get_state'):
            avatar_state = self.avatar_controller.get_state()
            base_status["avatar_state"] = avatar_state
        
        return base_status

# Global orchestrator instance
live_orchestrator = LiveCommerceOrchestrator()