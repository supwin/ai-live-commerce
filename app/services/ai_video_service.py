# app/services/ai_video_service.py
"""
AI Video Generation Service - Step 1 Implementation
สร้างวิดีโอจาก AI scripts พร้อม TTS audio integration
รองรับ 9:16 aspect ratio สำหรับ TikTok
"""

import asyncio
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import shutil

# Core imports
from sqlalchemy.orm import Session

# Video processing imports (ต้องติดตั้งก่อนใช้งาน)
try:
    from moviepy.editor import (
        VideoFileClip, ImageSequenceClip, concatenate_videoclips,
        TextClip, CompositeVideoClip, ColorClip, ImageClip
    )
    from moviepy.video.fx import resize, fadein, fadeout
    MOVIEPY_AVAILABLE = True
    print("✅ MoviePy available for video generation")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("⚠️ MoviePy not available - video generation will use simulation")

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
    print("✅ PIL available for image processing")
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available - using basic image processing")

# Local imports
from app.core.config import get_settings
from app.models.product import Product
from app.models.script import Script

class AIVideoService:
    """AI Video Generation Service - Step 1 Implementation"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Video configuration
        self.video_config = {
            "width": 1080,           # TikTok 9:16 width
            "height": 1920,          # TikTok 9:16 height
            "fps": 30,               # Frame rate
            "duration_per_slide": 3, # Seconds per text slide
            "transition_duration": 0.5, # Fade transition time
            "background_color": "#000000", # Black background
            "text_color": "#FFFFFF",       # White text
            "accent_color": "#FF6B6B"      # Red accent
        }
        
        # Directories
        self.video_dir = Path("frontend/uploads/videos")
        self.audio_dir = Path("frontend/static/audio")
        self.template_dir = Path("frontend/video_templates")
        self.temp_dir = Path("temp/video_generation")
        
        # Create directories
        for directory in [self.video_dir, self.template_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        print(f"🎬 AI Video Service initialized")
        print(f"   📁 Video output: {self.video_dir}")
        print(f"   🎵 Audio source: {self.audio_dir}")
        print(f"   🎨 Templates: {self.template_dir}")
        print(f"   💾 Temp files: {self.temp_dir}")
        print(f"   📐 Format: {self.video_config['width']}x{self.video_config['height']} (9:16)")
    
    async def generate_product_video(
        self,
        product_id: int,
        script: Dict[str, Any],
        db: Session,
        video_style: str = "slideshow",
        include_audio: bool = True
    ) -> Dict[str, Any]:
        """
        สร้างวิดีโอสินค้าจาก AI script
        
        Args:
            product_id: ID ของสินค้า
            script: ข้อมูลสคริปต์จาก AI
            db: Database session
            video_style: รูปแบบวิดีโอ (slideshow, animated_text, product_showcase)
            include_audio: รวม TTS audio หรือไม่
            
        Returns:
            Dict ที่มี video path และข้อมูลวิดีโอ
        """
        
        try:
            print(f"🎬 Starting video generation for product {product_id}")
            print(f"   📝 Script title: {script.get('title', 'Unknown')}")
            print(f"   🎨 Style: {video_style}")
            print(f"   🔊 Include audio: {include_audio}")
            
            # ดึงข้อมูลสินค้า
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # สร้าง unique video ID
            video_id = f"product_{product_id}_{int(time.time() * 1000)}"
            
            # เตรียมข้อมูลสำหรับสร้างวิดีโอ
            video_data = {
                "video_id": video_id,
                "product": product,
                "script": script,
                "style": video_style,
                "include_audio": include_audio
            }
            
            # สร้างวิดีโอตาม style ที่เลือก
            if video_style == "slideshow":
                result = await self._generate_slideshow_video(video_data)
            elif video_style == "animated_text":
                result = await self._generate_animated_text_video(video_data)
            elif video_style == "product_showcase":
                result = await self._generate_product_showcase_video(video_data)
            else:
                # Default to slideshow
                result = await self._generate_slideshow_video(video_data)
            
            # เพิ่ม audio หากต้องการ
            if include_audio and result.get("success"):
                audio_result = await self._add_audio_to_video(result, script, video_id)
                if audio_result.get("success"):
                    result.update(audio_result)
            
            print(f"✅ Video generation completed: {result.get('video_path', 'Unknown')}")
            return result
            
        except Exception as e:
            print(f"❌ Video generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "video_id": video_id if 'video_id' in locals() else None
            }
    
    async def _generate_slideshow_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """สร้างวิดีโอแบบ slideshow จากข้อมูลสินค้าและสคริปต์"""
        
        try:
            print("🎞️ Generating slideshow video...")
            
            if not MOVIEPY_AVAILABLE:
                return await self._simulate_video_generation(video_data, "slideshow")
            
            video_id = video_data["video_id"]
            product = video_data["product"]
            script = video_data["script"]
            
            # สร้างสไลด์ต่าง ๆ
            slides = []
            
            # Slide 1: Title slide
            title_slide = await self._create_title_slide(
                product.name,
                f"ราคา ฿{product.price:,.0f}",
                duration=4
            )
            slides.append(title_slide)
            
            # Slide 2: Product description
            description_slide = await self._create_text_slide(
                "รายละเอียดสินค้า",
                product.description or "สินค้าคุณภาพดี ราคาพิเศษ",
                duration=5
            )
            slides.append(description_slide)
            
            # Slide 3: Key features
            if product.key_features:
                features_text = "\n".join([f"✓ {feature}" for feature in product.key_features[:4]])
            else:
                features_text = "✓ คุณภาพดี\n✓ ราคาประหยัด\n✓ ใช้งานง่าย\n✓ ส่งฟรี"
                
            features_slide = await self._create_text_slide(
                "คุณสมบัติเด่น",
                features_text,
                duration=5
            )
            slides.append(features_slide)
            
            # Slide 4: Call to action
            cta_slide = await self._create_cta_slide(
                script.get("call_to_action", "สั่งซื้อได้เลยครับ!"),
                f"ราคาพิเศษ ฿{product.price:,.0f}",
                duration=4
            )
            slides.append(cta_slide)
            
            # รวมสไลด์เป็นวิดีโอ
            video_path = await self._combine_slides_to_video(slides, video_id)
            
            return {
                "success": True,
                "video_path": str(video_path),
                "video_id": video_id,
                "duration": len(slides) * self.video_config["duration_per_slide"],
                "format": "mp4",
                "resolution": f"{self.video_config['width']}x{self.video_config['height']}",
                "style": "slideshow",
                "slides_count": len(slides)
            }
            
        except Exception as e:
            print(f"❌ Slideshow generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_animated_text_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """สร้างวิดีโอแบบ animated text"""
        
        try:
            print("📝 Generating animated text video...")
            
            if not MOVIEPY_AVAILABLE:
                return await self._simulate_video_generation(video_data, "animated_text")
            
            video_id = video_data["video_id"]
            product = video_data["product"]
            script = video_data["script"]
            
            # แบ่งข้อความเป็นส่วน ๆ
            content = script.get("content", product.description or "สินค้าดีราคาคุ้มค่า")
            text_segments = self._split_text_to_segments(content)
            
            clips = []
            current_time = 0
            
            for i, segment in enumerate(text_segments):
                # สร้าง animated text clip
                text_clip = await self._create_animated_text_clip(
                    segment,
                    start_time=current_time,
                    duration=3,
                    animation_style="fade_in"
                )
                clips.append(text_clip)
                current_time += 3
            
            # Background
            background = ColorClip(
                size=(self.video_config["width"], self.video_config["height"]),
                color=self.video_config["background_color"],
                duration=current_time
            )
            
            # รวม clips
            final_video = CompositeVideoClip([background] + clips)
            
            # Export video
            video_path = self.video_dir / f"{video_id}_animated.mp4"
            final_video.write_videofile(
                str(video_path),
                fps=self.video_config["fps"],
                audio=False,
                verbose=False,
                logger=None
            )
            
            return {
                "success": True,
                "video_path": str(video_path),
                "video_id": video_id,
                "duration": current_time,
                "format": "mp4",
                "resolution": f"{self.video_config['width']}x{self.video_config['height']}",
                "style": "animated_text",
                "segments_count": len(text_segments)
            }
            
        except Exception as e:
            print(f"❌ Animated text generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _generate_product_showcase_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """สร้างวิดีโอแบบ product showcase"""
        
        try:
            print("🛍️ Generating product showcase video...")
            
            if not MOVIEPY_AVAILABLE:
                return await self._simulate_video_generation(video_data, "product_showcase")
            
            video_id = video_data["video_id"]
            product = video_data["product"]
            
            clips = []
            
            # Opening sequence
            opening = await self._create_opening_sequence(product.name, duration=3)
            clips.append(opening)
            
            # Product images (if available)
            if product.images:
                for i, image_path in enumerate(product.images[:3]):  # Max 3 images
                    image_clip = await self._create_image_showcase_clip(
                        image_path,
                        duration=4,
                        zoom_effect=True
                    )
                    clips.append(image_clip)
            
            # Features highlight
            features_clip = await self._create_features_highlight(
                product.key_features or ["คุณภาพดี", "ราคาประหยัด", "ส่งฟรี"],
                duration=6
            )
            clips.append(features_clip)
            
            # Price highlight
            price_clip = await self._create_price_highlight(
                product.price,
                getattr(product, 'original_price', None),
                duration=4
            )
            clips.append(price_clip)
            
            # รวม clips
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Export
            video_path = self.video_dir / f"{video_id}_showcase.mp4"
            final_video.write_videofile(
                str(video_path),
                fps=self.video_config["fps"],
                audio=False,
                verbose=False,
                logger=None
            )
            
            return {
                "success": True,
                "video_path": str(video_path),
                "video_id": video_id,
                "duration": final_video.duration,
                "format": "mp4",
                "resolution": f"{self.video_config['width']}x{self.video_config['height']}",
                "style": "product_showcase",
                "clips_count": len(clips)
            }
            
        except Exception as e:
            print(f"❌ Product showcase generation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _add_audio_to_video(
        self,
        video_result: Dict[str, Any],
        script: Dict[str, Any],
        video_id: str
    ) -> Dict[str, Any]:
        """เพิ่ม TTS audio ลงในวิดีโอ"""
        
        try:
            print("🔊 Adding TTS audio to video...")
            
            if not video_result.get("success"):
                return {"success": False, "error": "Video generation failed"}
            
            # Import TTS service
            try:
                from app.services.tts.enhanced_tts_service import enhanced_tts_service
            except ImportError:
                print("⚠️ TTS service not available - video without audio")
                return video_result
            
            # สร้าง TTS audio
            script_content = script.get("content", "สินค้าดีราคาคุ้มค่า")
            audio_result = await enhanced_tts_service.generate_script_audio(
                script_id=f"video_{video_id}",
                content=script_content,
                language="th"
            )
            
            if not audio_result[0]:  # audio_path is first element
                print("⚠️ TTS generation failed - keeping video without audio")
                return video_result
            
            audio_path = audio_result[0]
            video_path = video_result["video_path"]
            
            # Combine video + audio
            if MOVIEPY_AVAILABLE:
                video_with_audio_path = await self._combine_video_audio(
                    video_path,
                    audio_path,
                    video_id
                )
                
                return {
                    **video_result,
                    "video_path": video_with_audio_path,
                    "has_audio": True,
                    "audio_path": audio_path,
                    "tts_generated": True
                }
            else:
                # Simulation mode
                return {
                    **video_result,
                    "has_audio": True,
                    "audio_path": audio_path,
                    "tts_generated": True,
                    "note": "Audio generated but not combined (MoviePy not available)"
                }
                
        except Exception as e:
            print(f"❌ Audio addition failed: {str(e)}")
            return {
                **video_result,
                "audio_error": str(e),
                "has_audio": False
            }
    
    async def _combine_video_audio(
        self,
        video_path: str,
        audio_path: str,
        video_id: str
    ) -> str:
        """รวม video และ audio เข้าด้วยกัน"""
        
        try:
            if not MOVIEPY_AVAILABLE:
                return video_path
            
            video_clip = VideoFileClip(video_path)
            audio_clip = VideoFileClip(audio_path).audio if os.path.exists(audio_path) else None
            
            if audio_clip:
                # Adjust audio duration to match video
                if audio_clip.duration > video_clip.duration:
                    audio_clip = audio_clip.subclip(0, video_clip.duration)
                elif audio_clip.duration < video_clip.duration:
                    # Loop audio if shorter than video
                    loops_needed = int(video_clip.duration / audio_clip.duration) + 1
                    audio_clip = concatenate_audioclips([audio_clip] * loops_needed).subclip(0, video_clip.duration)
                
                final_video = video_clip.set_audio(audio_clip)
            else:
                final_video = video_clip
            
            # Export with audio
            output_path = self.video_dir / f"{video_id}_with_audio.mp4"
            final_video.write_videofile(
                str(output_path),
                fps=self.video_config["fps"],
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video_clip.close()
            if audio_clip:
                audio_clip.close()
            final_video.close()
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Video-audio combination failed: {str(e)}")
            return video_path
    
    async def _simulate_video_generation(
        self,
        video_data: Dict[str, Any],
        style: str
    ) -> Dict[str, Any]:
        """จำลองการสร้างวิดีโอเมื่อ MoviePy ไม่พร้อมใช้งาน"""
        
        print(f"🎭 Simulating {style} video generation...")
        
        video_id = video_data["video_id"]
        product = video_data["product"]
        
        # สร้างไฟล์ placeholder
        placeholder_path = self.video_dir / f"{video_id}_simulated.txt"
        
        simulation_data = {
            "video_id": video_id,
            "product_id": product.id,
            "product_name": product.name,
            "style": style,
            "generated_at": datetime.utcnow().isoformat(),
            "simulation": True,
            "note": "This is a simulated video generation. Install MoviePy for actual video creation."
        }
        
        with open(placeholder_path, 'w', encoding='utf-8') as f:
            json.dump(simulation_data, f, indent=2, ensure_ascii=False)
        
        return {
            "success": True,
            "video_path": str(placeholder_path),
            "video_id": video_id,
            "duration": 20,  # Estimated duration
            "format": "simulation",
            "resolution": f"{self.video_config['width']}x{self.video_config['height']}",
            "style": style,
            "simulation": True,
            "note": "MoviePy not available - simulation mode"
        }
    
    # Helper methods for video creation
    async def _create_title_slide(self, title: str, subtitle: str, duration: int):
        """สร้างสไลด์ title"""
        if not MOVIEPY_AVAILABLE:
            return None
            
        # Background
        bg = ColorClip(
            size=(self.video_config["width"], self.video_config["height"]),
            color=self.video_config["background_color"],
            duration=duration
        )
        
        # Title text
        title_clip = TextClip(
            title,
            fontsize=80,
            color=self.video_config["text_color"],
            font='Arial-Bold'
        ).set_position('center').set_duration(duration)
        
        # Subtitle text
        subtitle_clip = TextClip(
            subtitle,
            fontsize=50,
            color=self.video_config["accent_color"],
            font='Arial'
        ).set_position(('center', 'center+100')).set_duration(duration)
        
        return CompositeVideoClip([bg, title_clip, subtitle_clip])
    
    async def _create_text_slide(self, header: str, content: str, duration: int):
        """สร้างสไลด์ข้อความ"""
        if not MOVIEPY_AVAILABLE:
            return None
            
        bg = ColorClip(
            size=(self.video_config["width"], self.video_config["height"]),
            color=self.video_config["background_color"],
            duration=duration
        )
        
        header_clip = TextClip(
            header,
            fontsize=60,
            color=self.video_config["accent_color"],
            font='Arial-Bold'
        ).set_position(('center', 300)).set_duration(duration)
        
        content_clip = TextClip(
            content,
            fontsize=45,
            color=self.video_config["text_color"],
            font='Arial',
            size=(900, None),
            method='caption'
        ).set_position('center').set_duration(duration)
        
        return CompositeVideoClip([bg, header_clip, content_clip])
    
    async def _create_cta_slide(self, cta_text: str, price_text: str, duration: int):
        """สร้างสไลด์ Call to Action"""
        if not MOVIEPY_AVAILABLE:
            return None
            
        bg = ColorClip(
            size=(self.video_config["width"], self.video_config["height"]),
            color=self.video_config["accent_color"],
            duration=duration
        )
        
        cta_clip = TextClip(
            cta_text,
            fontsize=70,
            color="white",
            font='Arial-Bold'
        ).set_position('center').set_duration(duration)
        
        price_clip = TextClip(
            price_text,
            fontsize=80,
            color="yellow",
            font='Arial-Bold'
        ).set_position(('center', 'center+150')).set_duration(duration)
        
        return CompositeVideoClip([bg, cta_clip, price_clip])
    
    async def _combine_slides_to_video(self, slides: List, video_id: str) -> Path:
        """รวมสไลด์เป็นวิดีโอ"""
        if not MOVIEPY_AVAILABLE or not slides:
            # Create placeholder file
            placeholder_path = self.video_dir / f"{video_id}_placeholder.mp4"
            placeholder_path.touch()
            return placeholder_path
        
        # Add transitions
        clips_with_transitions = []
        for i, slide in enumerate(slides):
            if slide is None:
                continue
                
            if i > 0:
                slide = slide.crossfadein(self.video_config["transition_duration"])
            clips_with_transitions.append(slide)
        
        if not clips_with_transitions:
            placeholder_path = self.video_dir / f"{video_id}_empty.mp4"
            placeholder_path.touch()
            return placeholder_path
        
        # Concatenate
        final_video = concatenate_videoclips(clips_with_transitions, method="compose")
        
        # Export
        output_path = self.video_dir / f"{video_id}.mp4"
        final_video.write_videofile(
            str(output_path),
            fps=self.video_config["fps"],
            audio=False,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        final_video.close()
        for clip in clips_with_transitions:
            clip.close()
        
        return output_path
    
    def _split_text_to_segments(self, text: str, max_length: int = 100) -> List[str]:
        """แบ่งข้อความเป็นส่วน ๆ สำหรับ animation"""
        
        sentences = text.split('.')
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if len(current_segment + sentence) <= max_length:
                current_segment += sentence + ". "
            else:
                if current_segment:
                    segments.append(current_segment.strip())
                current_segment = sentence + ". "
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments or [text]
    
    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """ตรวจสอบสถานะวิดีโอ"""
        
        # ค้นหาไฟล์วิดีโอ
        possible_files = list(self.video_dir.glob(f"{video_id}*"))
        
        if not possible_files:
            return {
                "video_id": video_id,
                "exists": False,
                "status": "not_found"
            }
        
        video_file = possible_files[0]
        file_size = video_file.stat().st_size if video_file.exists() else 0
        
        return {
            "video_id": video_id,
            "exists": True,
            "status": "completed",
            "file_path": str(video_file),
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "created_at": datetime.fromtimestamp(video_file.stat().st_ctime).isoformat(),
            "is_simulation": video_file.suffix == ".txt"
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """ตรวจสอบสถานะของ service"""
        
        return {
            "service_name": "AI Video Service",
            "version": "1.0.0",
            "status": "active",
            "capabilities": {
                "moviepy_available": MOVIEPY_AVAILABLE,
                "pil_available": PIL_AVAILABLE,
                "video_generation": MOVIEPY_AVAILABLE,
                "simulation_mode": not MOVIEPY_AVAILABLE
            },
            "video_config": self.video_config,
            "directories": {
                "video_output": str(self.video_dir),
                "audio_source": str(self.audio_dir),
                "templates": str(self.template_dir),
                "temp": str(self.temp_dir)
            },
            "supported_styles": [
                "slideshow",
                "animated_text", 
                "product_showcase"
            ],
            "dependencies_status": {
                "moviepy": "✅ Available" if MOVIEPY_AVAILABLE else "❌ Not installed",
                "pil": "✅ Available" if PIL_AVAILABLE else "❌ Not installed"
            }
        }

# Global service instance
ai_video_service = AIVideoService()

# ตรวจสอบสถานะเมื่อ import
print("🎬 AI Video Service loaded")
status = ai_video_service.get_service_status()
if not MOVIEPY_AVAILABLE:
    print("📦 To enable video generation, install dependencies:")
    print("   pip install moviepy pillow")
print(f"🎯 Service ready in {'production' if MOVIEPY_AVAILABLE else 'simulation'} mode")