# app/services/ai_script_service.py
"""
AI Script Generation Service
Handles OpenAI integration for script generation with personas and emotional markup
"""

import json
import re
import time
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from openai import OpenAI
import asyncio
from datetime import datetime

from app.core.config import get_settings
from app.models.product import Product
from app.models.script import Script, ScriptPersona, ScriptType
from app.core.exceptions import AIServiceError, ValidationError

class AIScriptService:
    """AI-powered script generation service with emotional markup"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self._initialize_client()
        
        # Emotional markup tags for TTS
        self.emotion_tags = {
            "excited": {"open": "{excited}", "close": "{/excited}"},
            "happy": {"open": "{happy}", "close": "{/happy}"},
            "professional": {"open": "{professional}", "close": "{/professional}"},
            "confident": {"open": "{confident}", "close": "{/confident}"},
            "energetic": {"open": "{energetic}", "close": "{/energetic}"},
            "calm": {"open": "{calm}", "close": "{/calm}"},
            "warm": {"open": "{warm}", "close": "{/warm}"},
            "friendly": {"open": "{friendly}", "close": "{/friendly}"},
            "trustworthy": {"open": "{trustworthy}", "close": "{/trustworthy}"},
            "urgent": {"open": "{urgent}", "close": "{/urgent}"}
        }
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        try:
            if not self.settings.OPENAI_API_KEY:
                print("⚠️ WARNING: OPENAI_API_KEY not set. AI script generation will be simulated.")
                self.client = None
                return
                
            self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
            print("✅ OpenAI client initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI client: {e}")
            self.client = None
    
    async def generate_scripts(
        self,
        db: Session,
        product_id: int,
        persona_id: int,
        mood: str = "auto",
        count: int = 3,
        custom_instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple scripts for a product using AI with emotional markup
        
        Args:
            db: Database session
            product_id: Product ID
            persona_id: Script persona ID
            mood: Target mood/emotion
            count: Number of scripts to generate
            custom_instructions: Additional instructions
            
        Returns:
            List of generated script dictionaries
        """
        
        # Validate inputs
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValidationError("Product not found", field="product_id")
            
        persona = db.query(ScriptPersona).filter(ScriptPersona.id == persona_id).first()
        if not persona:
            raise ValidationError("Script persona not found", field="persona_id")
        
        if not persona.is_active:
            raise ValidationError("Script persona is inactive", field="persona_id")
        
        # Limit count
        count = max(1, min(count, 10))  # Between 1-10 scripts
        
        try:
            print(f"🤖 Generating {count} AI scripts for product {product.name} with persona {persona.name}")
            
            # Generate scripts
            generated_scripts = []
            
            for i in range(count):
                script_data = await self._generate_single_script(
                    product=product,
                    persona=persona,
                    mood=mood,
                    variation_number=i + 1,
                    custom_instructions=custom_instructions
                )
                
                if script_data:
                    # Save to database
                    script = self._save_script_to_db(
                        db=db,
                        product=product,
                        persona=persona,
                        script_data=script_data,
                        mood=mood
                    )
                    
                    generated_scripts.append(script.to_dict())
                    
                    # Small delay between requests
                    await asyncio.sleep(0.5)
            
            # Update persona usage statistics
            persona.usage_count += len(generated_scripts)
            if generated_scripts:
                # Calculate success rate
                persona.success_rate = (persona.usage_count / (persona.usage_count + 1)) * 100
            
            db.commit()
            
            print(f"✅ Generated {len(generated_scripts)} scripts successfully")
            return generated_scripts
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error generating scripts: {e}")
            raise AIServiceError("AI Script Generation", str(e))
    
    async def _generate_single_script(
        self,
        product: Product,
        persona: ScriptPersona,
        mood: str,
        variation_number: int,
        custom_instructions: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a single script with emotional markup"""
        
        try:
            # Build comprehensive prompt
            prompt = self._build_generation_prompt(
                product=product,
                persona=persona,
                mood=mood,
                variation_number=variation_number,
                custom_instructions=custom_instructions
            )
            
            # Generate with AI or simulate
            if self.client:
                content = await self._call_openai_api(prompt)
            else:
                content = self._simulate_script_generation(product, persona, mood, variation_number)
            
            # Parse and validate content
            script_data = self._parse_script_content(content, variation_number)
            
            # Add emotional markup
            script_data["content"] = self._add_emotional_markup(
                script_data["content"], 
                mood, 
                persona
            )
            
            return script_data
            
        except Exception as e:
            print(f"❌ Error generating single script: {e}")
            return None
    
    def _build_generation_prompt(
        self,
        product: Product,
        persona: ScriptPersona,
        mood: str,
        variation_number: int,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build comprehensive prompt for script generation"""
        
        # Determine target emotion
        target_emotion = mood if mood != "auto" else persona.default_emotion
        
        # Build product information
        product_info = {
            "name": product.name,
            "price": f"฿{product.price:,.2f}",
            "description": product.description or "",
            "key_features": product.key_features or [],
            "selling_points": product.selling_points or [],
            "target_audience": product.target_audience or "",
            "category": product.category or "",
            "brand": product.brand or "",
            "promotion": product.promotion_text or ""
        }
        
        # Special pricing info
        pricing_info = ""
        if product.is_on_sale:
            pricing_info = f"""
SPECIAL PROMOTION:
- Original Price: ฿{product.original_price:,.2f}
- Sale Price: ฿{product.sale_price:,.2f}
- Discount: {product.discount_percentage}% OFF
- Promotion Text: {product.promotion_text or 'Limited time offer!'}
"""
        
        # Build comprehensive prompt
        prompt = f"""
{persona.system_prompt}

TARGET EMOTION: {target_emotion}
SCRIPT VARIATION: #{variation_number} (make each script unique)

PRODUCT INFORMATION:
Name: {product_info['name']}
Price: {product_info['price']}
Category: {product_info['category']}
Brand: {product_info['brand']}

{pricing_info}

Description: {product_info['description']}

Key Features:
{chr(10).join(f"• {feature}" for feature in product_info['key_features'])}

Selling Points:
{chr(10).join(f"• {point}" for point in product_info['selling_points'])}

Target Audience: {product_info['target_audience']}

PERSONA GUIDELINES:
Speaking Style: {persona.speaking_style}
Personality Traits: {', '.join(persona.traits_list)}
Target Audience: {persona.target_audience}

Tone Guidelines: {persona.tone_guidelines or 'Professional and engaging'}

DO SAY (encourage these phrases):
{chr(10).join(f"• {phrase}" for phrase in (persona.do_say or []))}

DON'T SAY (avoid these phrases):
{chr(10).join(f"• {phrase}" for phrase in (persona.dont_say or []))}

EMOTIONAL REQUIREMENTS:
- Target Emotion: {target_emotion}
- Express this emotion naturally throughout the script
- Use appropriate emotional language and expressions
- Build emotional connection with the audience

SCRIPT STRUCTURE REQUIREMENTS:
1. TITLE: Create an engaging title (max 100 characters)
2. CONTENT: Write the main script content (150-300 words)
3. CTA: Include a strong call-to-action

CONTENT GUIDELINES:
- Write in Thai language (unless specified otherwise)
- Duration: Aim for 45-90 seconds when spoken
- Include specific product details and benefits
- Address the target audience directly
- Create urgency if there's a promotion
- End with a clear call-to-action
- Make script #{variation_number} unique from others

EMOTIONAL EXPRESSIONS FOR {target_emotion.upper()}:
- Use words and phrases that convey {target_emotion}
- Adjust pace and rhythm to match the emotion
- Include appropriate exclamations or emphasis
- Build emotional momentum throughout the script

{f"CUSTOM INSTRUCTIONS: {custom_instructions}" if custom_instructions else ""}

RESPONSE FORMAT:
Return only a JSON object with this exact structure:
{{
    "title": "Engaging script title here",
    "content": "Main script content in Thai...",
    "call_to_action": "Strong call to action",
    "estimated_duration": 60,
    "target_emotion": "{target_emotion}",
    "key_points": ["point1", "point2", "point3"]
}}

DO NOT include any text outside the JSON object. DO NOT use markdown formatting.
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI API for script generation"""
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert Thai live commerce script writer. Generate engaging, emotional scripts that drive sales. Always return valid JSON responses."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.settings.OPENAI_TEMPERATURE,
                max_tokens=self.settings.OPENAI_MAX_TOKENS * 3,  # Longer scripts
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # Validate JSON response
            try:
                json.loads(content)
                return content
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON from OpenAI, attempting to fix...")
                return self._fix_json_response(content)
                
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            raise AIServiceError("OpenAI API", str(e))
    
    def _fix_json_response(self, content: str) -> str:
        """Attempt to fix malformed JSON response"""
        try:
            # Remove markdown formatting
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'\s*```', '', content)
            
            # Try to parse again
            json.loads(content)
            return content
            
        except:
            # Return fallback JSON
            return json.dumps({
                "title": "Product Presentation Script",
                "content": "สวัสดีครับทุกคน! วันนี้มีสินค้าพิเศษมาแนะนำให้เพื่อนๆ ครับ สินค้าคุณภาพดี ราคาดี ไม่ควรพลาด!",
                "call_to_action": "สั่งซื้อเลยครับ!",
                "estimated_duration": 45,
                "target_emotion": "friendly",
                "key_points": ["คุณภาพดี", "ราคาดี", "ไม่ควรพลาด"]
            })
    
    def _simulate_script_generation(
        self, 
        product: Product, 
        persona: ScriptPersona, 
        mood: str, 
        variation_number: int
    ) -> str:
        """Simulate AI script generation when OpenAI is not available"""
        
        # Determine emotion
        emotion = mood if mood != "auto" else persona.default_emotion
        
        # Create variations based on number
        variations = {
            1: {
                "style": "เปิดด้วยการทักทาย",
                "approach": "เน้นคุณสมบัติเด่น",
                "energy": "กระตือรือร้น"
            },
            2: {
                "style": "เปิดด้วยปัญหาที่แก้ได้",
                "approach": "เน้นประโยชน์ที่ได้รับ", 
                "energy": "เป็นมิตร"
            },
            3: {
                "style": "เปิดด้วยโปรโมชั่น",
                "approach": "เน้นความคุ้มค่า",
                "energy": "เร่งด่วน"
            }
        }
        
        var = variations.get(variation_number, variations[1])
        
        # Build simulated content
        greeting = self._get_greeting_by_emotion(emotion)
        product_intro = self._build_product_introduction(product, var["approach"])
        features = self._build_features_section(product, emotion)
        pricing = self._build_pricing_section(product, emotion)
        closing = self._get_closing_by_emotion(emotion)
        
        content = f"""{greeting}

{product_intro}

{features}

{pricing}

{closing}"""
        
        # Estimate duration (150 words per minute)
        word_count = len(content.split())
        duration = max(30, int(word_count / 2.5))  # 2.5 words per second
        
        return json.dumps({
            "title": f"{product.name} - {var['style']} (สคริปต์ที่ {variation_number})",
            "content": content.strip(),
            "call_to_action": self._generate_cta(product, emotion),
            "estimated_duration": duration,
            "target_emotion": emotion,
            "key_points": [
                f"เน้น{var['approach']}",
                f"อารมณ์{emotion}",
                f"ระยะเวลา ~{duration} วินาที"
            ]
        }, ensure_ascii=False)
    
    def _get_greeting_by_emotion(self, emotion: str) -> str:
        """Get appropriate greeting based on emotion"""
        greetings = {
            "excited": "สวัสดีครับทุกคน! 🎉 วันนี้มีข่าวดีมาแชร์กันครับ!",
            "professional": "สวัสดีครับ ยินดีต้อนรับทุกท่านสู่การนำเสนอสินค้าพิเศษ",
            "friendly": "สวัสดีครับเพื่อนๆ 😊 มาเจอกันอีกแล้วนะครับ",
            "confident": "สวัสดีครับ! วันนี้เรามีสินค้าสุดพิเศษที่รับรองว่าคุณจะต้องชอบ",
            "energetic": "สวัสดีครับทุกคน! ⚡ พร้อมแล้วสำหรับของดีราคาดีกันมั้ยครับ!",
            "calm": "สวัสดีครับทุกท่าน อยากแนะนำสินค้าดีๆ ให้ทุกคนได้รู้จักครับ",
            "urgent": "สวัสดีครับ! 🔥 โอกาสพิเศษที่ไม่ควรพลาดกำลังจะมาแล้ว!"
        }
        return greetings.get(emotion, greetings["professional"])
    
    def _build_product_introduction(self, product: Product, approach: str) -> str:
        """Build product introduction based on approach"""
        name = product.name
        category = product.category or "สินค้า"
        
        if "คุณสมบัติ" in approach:
            return f"วันนี้ขอแนะนำ {name} ที่มาพร้อมกับคุณสมบัติเด่นที่จะทำให้ชีวิตของคุณดีขึ้น"
        elif "ประโยชน์" in approach:
            return f"คุณเคยมีปัญหากับ{category}มั้ยครับ? วันนี้เรามี {name} ที่จะช่วยแก้ปัญหาเหล่านั้นได้"
        elif "ความคุ้มค่า" in approach:
            return f"ถ้าคุณกำลังมองหา{category}คุณภาพดี ราคาดี {name} คือคำตอบที่คุณต้องการ"
        else:
            return f"ขอแนะนำ {name} สินค้าคุณภาพที่คุณไม่ควรพลาด"
    
    def _build_features_section(self, product: Product, emotion: str) -> str:
        """Build features section based on emotion"""
        features = product.key_features or ["คุณภาพดี", "ใช้งานง่าย", "คุ้มค่า"]
        
        if emotion in ["excited", "energetic"]:
            intro = "ฟีเจอร์เด็ดๆ ที่ทำให้สินค้าชิ้นนี้พิเศษมากๆ ครับ!"
            bullet = "🌟"
        elif emotion == "professional":
            intro = "คุณสมบัติสำคัญของสินค้าชิ้นนี้ ได้แก่:"
            bullet = "•"
        elif emotion == "confident":
            intro = "สิ่งที่ทำให้เราภูมิใจในสินค้าชิ้นนี้คือ:"
            bullet = "✓"
        else:
            intro = "จุดเด่นของสินค้าที่อยากให้ทุกคนรู้:"
            bullet = "•"
        
        feature_list = "\n".join([f"{bullet} {feature}" for feature in features[:4]])
        
        return f"{intro}\n{feature_list}"
    
    def _build_pricing_section(self, product: Product, emotion: str) -> str:
        """Build pricing section with emotional appeal"""
        
        if product.is_on_sale:
            if emotion in ["excited", "urgent"]:
                return f"""🔥 โปรโมชั่นพิเศษ! 🔥
ราคาปกติ {product.original_price:,.0f} บาท
ลดเหลือเพียง {product.sale_price:,.0f} บาท!
ประหยัดไปเลย {product.original_price - product.sale_price:,.0f} บาท!"""
            else:
                return f"""ราคาพิเศษสำหรับวันนี้
จากราคา {product.original_price:,.0f} บาท ลดเหลือ {product.sale_price:,.0f} บาท
คุ้มค่ามากครับ!"""
        else:
            if emotion == "confident":
                return f"ราคาเพียง {product.price:,.0f} บาท คุ้มค่าทุกบาทที่จ่าย"
            else:
                return f"ราคาเพียง {product.price:,.0f} บาท ครับ"
    
    def _get_closing_by_emotion(self, emotion: str) -> str:
        """Get appropriate closing based on emotion"""
        closings = {
            "excited": "อย่าลังเลนะครับ! โอกาสดีๆ แบบนี้ไม่มีบ่อยหรอก! 🎯",
            "professional": "ขอเชิญสั่งซื้อได้เลยครับ เราพร้อมให้บริการด้วยความใส่ใจ",
            "friendly": "ถ้าสนใจก็สั่งได้เลยนะครับ รับรองว่าคุ้มค่าแน่นอน 😊",
            "confident": "เราเชื่อมั่นว่าคุณจะพอใจ สั่งซื้อได้เลยครับ!",
            "energetic": "มาสิครับ! พลาดแล้วเสียดายแน่! ⚡",
            "calm": "สนใจสามารถสั่งซื้อได้ครับ ขอบคุณที่รับฟังครับ",
            "urgent": "รีบสั่งก่อนที่จะหมดนะครับ! เหลือไม่เยอะแล้ว! ⏰"
        }
        return closings.get(emotion, closings["professional"])
    
    def _generate_cta(self, product: Product, emotion: str) -> str:
        """Generate call-to-action based on emotion"""
        ctas = {
            "excited": "สั่งเลย! ไม่สั่งเสียดาย! 🛒",
            "professional": "สั่งซื้อได้ทันทีครับ",
            "friendly": "ลองสั่งดูนะครับ 😊",
            "confident": "สั่งซื้อเลยครับ รับรองไม่ผิดหวัง!",
            "energetic": "กดสั่งเลย! ตอนนี้เลย! ⚡",
            "calm": "สั่งซื้อได้ครับ",
            "urgent": "รีบสั่งก่อนหมด! 🔥"
        }
        return ctas.get(emotion, "สั่งซื้อได้เลยครับ")
    
    def _parse_script_content(self, content: str, variation_number: int) -> Dict[str, Any]:
        """Parse and validate script content"""
        try:
            data = json.loads(content)
            
            # Validate required fields
            required_fields = ["title", "content"]
            for field in required_fields:
                if field not in data or not data[field]:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set defaults for optional fields
            data.setdefault("call_to_action", "สั่งซื้อได้เลยครับ!")
            data.setdefault("estimated_duration", 60)
            data.setdefault("target_emotion", "professional")
            data.setdefault("key_points", [])
            
            # Add variation suffix to title if not unique
            if f"ที่ {variation_number}" not in data["title"]:
                data["title"] = f"{data['title']} (เวอร์ชั่น {variation_number})"
            
            return data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON content: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing script content: {e}")
    
    def _add_emotional_markup(self, content: str, mood: str, persona: ScriptPersona) -> str:
        """Add emotional markup tags for TTS processing"""
        
        # Determine target emotion
        target_emotion = mood if mood != "auto" else persona.default_emotion
        
        # Skip if emotion not supported
        if target_emotion not in self.emotion_tags:
            return content
        
        # Get emotion tags
        emotion_tag = self.emotion_tags[target_emotion]
        
        # Split content into sentences
        sentences = re.split(r'[.!?]\s*', content)
        marked_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                # Identify emotional phrases
                marked_sentence = self._mark_emotional_phrases(
                    sentence.strip(), 
                    target_emotion, 
                    emotion_tag
                )
                marked_sentences.append(marked_sentence)
        
        # Join back with periods
        marked_content = '. '.join(marked_sentences)
        
        # Add overall emotional wrapper for key sections
        marked_content = self._wrap_key_sections(marked_content, emotion_tag, target_emotion)
        
        return marked_content
    
    def _mark_emotional_phrases(self, sentence: str, emotion: str, emotion_tag: Dict) -> str:
        """Mark specific phrases with emotional tags"""
        
        # Define emotional trigger phrases for each emotion
        emotional_phrases = {
            "excited": [
                r"(สุดยอด|เจ๋งมาก|วาว|เยี่ยมมาก|ดีเลิศ)",
                r"(โอกาสทอง|พิเศษมาก|ไม่ควรพลาด)",
                r"(ลดราคา|โปรโมชั่น|ส่วนลด)"
            ],
            "confident": [
                r"(รับรอง|การันตี|มั่นใจ|แน่นอน)",
                r"(คุณภาพดี|มาตรฐาน|เชื่อถือได้)",
                r"(ผู้เชี่ยวชาญ|มืออาชีพ|ประสบการณ์)"
            ],
            "urgent": [
                r"(รีบ|เร่งด่วน|จำกัด|หมดเขต)",
                r"(เหลือไม่เยอะ|ของมีจำกัด|โอกาสสุดท้าย)",
                r"(วันนี้เท่านั้น|ตอนนี้เลย|ก่อนหมด)"
            ],
            "friendly": [
                r"(เพื่อนๆ|ทุกคน|น้องๆ|พี่ๆ)",
                r"(น่ารัก|น่าใช้|ดีจริง)",
                r"(แนะนำ|แชร์|บอกต่อ)"
            ]
        }
        
        phrases = emotional_phrases.get(emotion, [])
        
        for pattern in phrases:
            sentence = re.sub(
                pattern,
                f"{emotion_tag['open']}\\1{emotion_tag['close']}",
                sentence,
                flags=re.IGNORECASE
            )
        
        return sentence
    
    def _wrap_key_sections(self, content: str, emotion_tag: Dict, emotion: str) -> str:
        """Wrap key sections with emotional tags"""
        
        # Mark call-to-action phrases
        cta_patterns = [
            r"(สั่ง.*?ได้.*?เลย.*?ครับ|กดสั่ง.*?เลย|รีบสั่ง.*?ครับ)",
            r"(อย่า.*?พลาด.*?ครับ|ไม่.*?ควร.*?พลาด)",
            r"(ลอง.*?ดู.*?ครับ|ทดลอง.*?ใช้)"
        ]
        
        for pattern in cta_patterns:
            content = re.sub(
                pattern,
                f"{emotion_tag['open']}\\1{emotion_tag['close']}",
                content,
                flags=re.IGNORECASE
            )
        
        return content
    
    def _save_script_to_db(
        self,
        db: Session,
        product: Product,
        persona: ScriptPersona,
        script_data: Dict[str, Any],
        mood: str
    ) -> Script:
        """Save generated script to database"""
        
        # Calculate estimated duration more accurately
        word_count = len(script_data["content"].split())
        duration_estimate = max(30, int(word_count / 2.5))  # 2.5 words per second
        
        script = Script(
            product_id=product.id,
            title=script_data["title"],
            content=script_data["content"],
            script_type=ScriptType.AI_GENERATED,
            persona_id=persona.id,
            language="th",
            target_emotion=script_data.get("target_emotion", mood),
            tone=persona.speaking_style,
            call_to_action=script_data.get("call_to_action", ""),
            duration_estimate=duration_estimate,
            generation_model=self.settings.OPENAI_MODEL,
            generation_temperature=self.settings.OPENAI_TEMPERATURE,
            generation_prompt=f"Generated with persona: {persona.name}, mood: {mood}"
        )
        
        db.add(script)
        db.flush()  # Get the ID
        
        return script
    
    async def enhance_existing_script(
        self,
        db: Session,
        script_id: int,
        enhancement_type: str = "emotional",
        target_emotion: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Enhance an existing script with better emotional markup or content"""
        
        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise ValidationError("Script not found", field="script_id")
        
        if not script.can_edit:
            raise ValidationError("Script cannot be edited (has MP3)", field="script_id")
        
        try:
            original_content = script.content
            
            if enhancement_type == "emotional":
                # Add or improve emotional markup
                emotion = target_emotion or script.target_emotion or "professional"
                enhanced_content = self._add_emotional_markup(
                    original_content, 
                    emotion, 
                    script.persona
                )
                
            elif enhancement_type == "content":
                # Use AI to improve content quality
                if self.client:
                    enhanced_content = await self._enhance_content_with_ai(script)
                else:
                    enhanced_content = self._enhance_content_manually(script)
            
            else:
                raise ValidationError("Invalid enhancement type", field="enhancement_type")
            
            # Update script
            script.content = enhanced_content
            if target_emotion:
                script.target_emotion = target_emotion
            
            db.commit()
            
            return script.to_dict()
            
        except Exception as e:
            db.rollback()
            raise AIServiceError("Script Enhancement", str(e))
    
    async def _enhance_content_with_ai(self, script: Script) -> str:
        """Use AI to enhance script content quality"""
        
        prompt = f"""
Enhance this Thai live commerce script to make it more engaging and persuasive.
Keep the same length and main message, but improve the language, flow, and emotional appeal.

Original Script:
{script.content}

Target Emotion: {script.target_emotion}
Persona Style: {script.persona.speaking_style if script.persona else 'Professional'}

Make it more engaging while maintaining the original meaning.
Return only the enhanced script content, no explanations.
"""
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert at enhancing Thai live commerce scripts. Make them more engaging and persuasive."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Error enhancing content with AI: {e}")
            return script.content  # Return original if enhancement fails
    
    def _enhance_content_manually(self, script: Script) -> str:
        """Manually enhance script content"""
        content = script.content
        
        # Simple enhancements
        enhancements = [
            (r'\bดี\b', 'ดีเลิศ'),
            (r'\bเยี่ยม\b', 'เยี่ยมมาก'),
            (r'\bสั่งซื้อ\b', 'สั่งซื้อได้เลย'),
            (r'\bคุ้มค่า\b', 'คุ้มค่ามากๆ'),
            (r'\bราคาดี\b', 'ราคาดีเยี่ยม')
        ]
        
        for pattern, replacement in enhancements:
            content = re.sub(pattern, replacement, content)
        
        return content

# Global service instance
ai_script_service = AIScriptService()