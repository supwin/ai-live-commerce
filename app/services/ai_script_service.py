# app/services/ai_script_service.py
"""
AI Script Generation Service - FIXED VERSION
Enhanced OpenAI integration for real script generation with comprehensive error handling
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
from app.models.script import Script, ScriptPersona, ScriptType, ScriptStatus
from app.core.exceptions import AIServiceError, ValidationError

class AIScriptService:
    """AI-powered script generation service with real OpenAI integration"""
    
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
        """Initialize OpenAI client with proper error handling"""
        try:
            api_key = self.settings.OPENAI_API_KEY
            
            if not api_key or api_key.strip() == "":
                print("⚠️ WARNING: OPENAI_API_KEY not set or empty. AI script generation will use mock data.")
                self.client = None
                return
                
            if not api_key.startswith('sk-'):
                print(f"⚠️ WARNING: Invalid OpenAI API key format. Expected format: sk-...")
                self.client = None
                return
                
            # Initialize OpenAI client
            self.client = OpenAI(api_key=api_key)
            
            # Test the connection with a simple request
            try:
                test_response = self.client.models.list()
                print("✅ OpenAI client initialized and tested successfully")
                print(f"📊 Available models: {len(test_response.data)} models")
                
                # Check if the configured model is available
                available_models = [model.id for model in test_response.data]
                if self.settings.OPENAI_MODEL not in available_models:
                    print(f"⚠️ WARNING: Configured model '{self.settings.OPENAI_MODEL}' not available")
                    print(f"📋 Available models include: gpt-3.5-turbo, gpt-4, gpt-4-turbo-preview")
                    # Use gpt-3.5-turbo as fallback
                    self.settings.OPENAI_MODEL = "gpt-3.5-turbo"
                    print(f"🔄 Using fallback model: {self.settings.OPENAI_MODEL}")
                
            except Exception as test_error:
                print(f"⚠️ OpenAI connection test failed: {test_error}")
                print("🔧 Please verify your API key and internet connection")
                self.client = None
                
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
        Generate multiple scripts for a product using AI with real OpenAI integration
        """
        
        print(f"🤖 Starting AI script generation...")
        print(f"📊 Parameters: product_id={product_id}, persona_id={persona_id}, mood={mood}, count={count}")
        
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
            print(f"🎯 Generating {count} AI scripts for product '{product.name}' with persona '{persona.name}'")
            
            # Check if OpenAI is available
            if not self.client:
                print("⚠️ OpenAI not available, using simulation")
                return await self._generate_with_simulation(db, product, persona, mood, count, custom_instructions)
            
            # Generate scripts using real OpenAI
            generated_scripts = []
            
            for i in range(count):
                print(f"🔄 Generating script {i+1}/{count}...")
                
                script_data = await self._generate_single_script_openai(
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
                    print(f"✅ Script {i+1} generated successfully: {script_data['title'][:50]}...")
                    
                    # Small delay between requests to respect rate limits
                    await asyncio.sleep(1)
                else:
                    print(f"❌ Failed to generate script {i+1}")
            
            # Update persona usage statistics
            persona.usage_count = (persona.usage_count or 0) + len(generated_scripts)
            if generated_scripts:
                # Calculate success rate
                total_attempts = (persona.usage_count or 0)
                persona.success_rate = 100.0  # All generated scripts are successful
            
            # Commit all changes at once
            db.commit()
            db.refresh(persona)  # Refresh persona object
            
            # Refresh all scripts to get latest data
            for script_dict in generated_scripts:
                script_obj = db.query(Script).filter(Script.id == script_dict['id']).first()
                if script_obj:
                    db.refresh(script_obj)
            
            print(f"🎉 Generated {len(generated_scripts)} scripts successfully!")
            return generated_scripts
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error generating scripts: {e}")
            raise AIServiceError("AI Script Generation", str(e))
    
    async def _generate_single_script_openai(
        self,
        product: Product,
        persona: ScriptPersona,
        mood: str,
        variation_number: int,
        custom_instructions: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Generate a single script using real OpenAI API"""
        
        try:
            # Build comprehensive prompt
            prompt = self._build_enhanced_generation_prompt(
                product=product,
                persona=persona,
                mood=mood,
                variation_number=variation_number,
                custom_instructions=custom_instructions
            )
            
            print(f"🔤 Prompt length: {len(prompt)} characters")
            
            # Call OpenAI API
            response = await self._call_openai_api_with_retry(prompt)
            
            if not response:
                print("❌ No response from OpenAI")
                return None
            
            # Parse and validate content
            script_data = self._parse_and_validate_response(response, variation_number)
            
            # Add emotional markup
            if script_data and script_data.get("content"):
                script_data["content"] = self._add_emotional_markup(
                    script_data["content"], 
                    mood, 
                    persona
                )
            
            return script_data
            
        except Exception as e:
            print(f"❌ Error generating single script: {e}")
            return None
    
    def _build_enhanced_generation_prompt(
        self,
        product: Product,
        persona: ScriptPersona,
        mood: str,
        variation_number: int,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build comprehensive and effective prompt for OpenAI"""
        
        # Determine target emotion
        target_emotion = mood if mood != "auto" else (persona.default_emotion if hasattr(persona, 'default_emotion') else "professional")
        
        # Build product information
        key_features = product.key_features or []
        selling_points = product.selling_points or []
        
        # Special pricing info
        pricing_section = ""
        if hasattr(product, 'is_on_sale') and product.is_on_sale:
            original_price = getattr(product, 'original_price', float(product.price) * 1.2)
            discount = getattr(product, 'discount_percentage', 20)
            pricing_section = f"""
🔥 SPECIAL PROMOTION:
- ราคาปกติ: ฿{float(original_price):,.0f}
- ราคาพิเศษ: ฿{float(product.price):,.0f}
- ส่วนลด: {discount}% OFF
- โปรโมชั่น: {getattr(product, 'promotion_text', 'ข้อเสนอพิเศษในช่วงเวลาจำกัด!')}
"""
        
        # Build the main prompt
        prompt = f"""คุณเป็นนักเขียนสคริปต์ live commerce ภาษาไทยมืออาชีพ เชี่ยวชาญการสร้างสคริปต์ที่กระตุ้นการขายและสร้างอารมณ์ให้ผู้ชม

=== ข้อมูลสินค้า ===
ชื่อสินค้า: {product.name}
ราคา: ฿{product.price:,.0f}
หมวดหมู่: {product.category or 'สินค้าทั่วไป'}
แบรนด์: {product.brand or 'แบรนด์คุณภาพ'}

{pricing_section}

รายละเอียดสินค้า:
{product.description or 'สินค้าคุณภาพดีที่คุ้มค่าการใช้งาน'}

คุณสมบัติเด่น:
{chr(10).join(f'• {feature}' for feature in key_features) if key_features else '• คุณภาพดี ใช้งานได้จริง'}

จุดขาย:
{chr(10).join(f'• {point}' for point in selling_points) if selling_points else '• เหมาะสำหรับทุกคน ราคาคุ้มค่า'}

กลุ่มเป้าหมาย: {product.target_audience or 'คนทั่วไปที่ต้องการสินค้าคุณภาพ'}

=== บุคลิกผู้นำเสนอ ===
ชื่อ Persona: {persona.name}
รายละเอียด: {persona.description or 'ผู้นำเสนอมืออาชีพ'}
ลักษณะการพูด: {persona.speaking_style or 'เป็นมิตรและมั่นใจ'}
กลุ่มเป้าหมาย: {persona.target_audience or 'ลูกค้าทั่วไป'}

=== อารมณ์เป้าหมาย ===
อารมณ์หลัก: {target_emotion}
ความรู้สึกที่ต้องการสร้าง: {target_emotion}

=== คำแนะนำการเขียน ===
{persona.system_prompt if hasattr(persona, 'system_prompt') else 'เขียนสคริปต์ที่น่าสนใจ ใช้คำพูดที่เป็นธรรมชาติ เน้นประโยชน์ของสินค้า'}

=== สคริปต์เวอร์ชั่น ===
เวอร์ชั่นที่: {variation_number} (ทำให้แต่ละเวอร์ชั่นมีความแตกต่างกัน)

{f"=== คำแนะนำเพิ่มเติม ==={chr(10)}{custom_instructions}" if custom_instructions else ""}

=== ข้อกำหนดสคริปต์ ===
1. ใช้ภาษาไทยที่เป็นธรรมชาติ
2. ระยะเวลา: 60-90 วินาที เมื่ออ่านออกเสียง
3. โครงสร้าง: เปิด → แนะนำสินค้า → คุณสมบัติ → ราคา/โปรโมชั่น → ปิดการขาย
4. สร้างความตื่นเต้นและความเชื่อใจ
5. มี Call-to-Action ที่ชัดเจน
6. เหมาะสำหรับการถ่ายทอดสด
7. แต่ละเวอร์ชั่นต้องมีการเริ่มต้นและสิ้นสุดที่แตกต่างกัน

=== รูปแบบการตอบ ===
กรุณาตอบเป็น JSON format เท่านั้น ไม่ต้องมีคำอธิบายอื่น

{{
    "title": "ชื่อสคริปต์ที่น่าสนใจ (ไม่เกิน 100 ตัวอักษร)",
    "content": "เนื้อหาสคริปต์ภาษาไทยที่สมบูรณ์ (150-300 คำ)",
    "call_to_action": "ประโยคเรียกร้องให้สั่งซื้อ",
    "estimated_duration": 75,
    "target_emotion": "{target_emotion}",
    "key_points": ["จุดเด่น 1", "จุดเด่น 2", "จุดเด่น 3"]
}}

สำคัญ: ตอบเป็น JSON เท่านั้น เริ่มด้วย {{ และจบด้วย }} ไม่ต้องมี ```json"""
        
        return prompt
    
    async def _call_openai_api_with_retry(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Call OpenAI API with retry logic and proper error handling"""
        
        for attempt in range(max_retries):
            try:
                print(f"🔄 OpenAI API call attempt {attempt + 1}/{max_retries}")
                
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.settings.OPENAI_MODEL,
                    messages=[
                        {
                            "role": "system", 
                            "content": "คุณเป็นผู้เชี่ยวชาญด้านการเขียนสคริปต์ live commerce ภาษาไทย ที่สามารถสร้างเนื้อหาที่น่าสนใจและกระตุ้นการขายได้อย่างมีประสิทธิภาพ กรุณาตอบเป็น JSON format เสมอ"
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.settings.OPENAI_TEMPERATURE,
                    max_tokens=1500,  # Increased for longer scripts
                    top_p=0.9,
                    frequency_penalty=0.1,  # Reduce repetition
                    presence_penalty=0.1   # Encourage creativity
                )
                
                content = response.choices[0].message.content.strip()
                
                if content:
                    print("✅ Successfully received response from OpenAI")
                    print(f"📝 Response preview: {content[:100]}...")
                    return content
                else:
                    print(f"⚠️ Empty response from OpenAI (attempt {attempt + 1})")
                    
            except Exception as e:
                print(f"❌ OpenAI API error (attempt {attempt + 1}): {e}")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    print(f"⏳ Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    print("❌ All OpenAI API attempts failed")
                    return None
        
        return None
    
    def _parse_and_validate_response(self, content: str, variation_number: int) -> Optional[Dict[str, Any]]:
        """Parse and validate OpenAI response with better error handling"""
        
        try:
            # Clean the content
            content = content.strip()
            
            # Remove any markdown formatting
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            
            # Find JSON boundaries
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                print(f"❌ No JSON found in response: {content[:200]}")
                return self._create_fallback_script(variation_number)
            
            json_content = content[start_idx:end_idx + 1]
            
            # Try to parse JSON
            try:
                data = json.loads(json_content)
                print("✅ Successfully parsed JSON from OpenAI response")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"📝 Problematic content: {json_content[:300]}")
                return self._create_fallback_script(variation_number)
            
            # Validate required fields
            required_fields = ["title", "content"]
            for field in required_fields:
                if field not in data or not data[field] or not isinstance(data[field], str):
                    print(f"❌ Missing or invalid required field: {field}")
                    return self._create_fallback_script(variation_number)
            
            # Set defaults for optional fields
            data.setdefault("call_to_action", "สั่งซื้อได้เลยครับ!")
            data.setdefault("estimated_duration", 60)
            data.setdefault("target_emotion", "professional")
            data.setdefault("key_points", [])
            
            # Ensure key_points is a list
            if not isinstance(data.get("key_points"), list):
                data["key_points"] = []
            
            # Validate content length (should be reasonable for 60-90 seconds)
            word_count = len(data["content"].split())
            if word_count < 30:
                print(f"⚠️ Content too short: {word_count} words")
                return self._create_fallback_script(variation_number)
            elif word_count > 500:
                print(f"⚠️ Content too long: {word_count} words, truncating...")
                words = data["content"].split()[:300]
                data["content"] = " ".join(words) + "... สั่งซื้อได้เลยครับ!"
            
            # Update estimated duration based on word count
            data["estimated_duration"] = max(45, min(120, int(word_count / 2.5)))  # 2.5 words per second
            
            print(f"✅ Validated script: {data['title'][:50]}... ({word_count} words, ~{data['estimated_duration']}s)")
            return data
            
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return self._create_fallback_script(variation_number)
    
    def _create_fallback_script(self, variation_number: int) -> Dict[str, Any]:
        """Create a fallback script when OpenAI fails"""
        
        fallback_scripts = [
            {
                "title": f"สคริปต์แนะนำสินค้า (เวอร์ชั่น {variation_number})",
                "content": "สวัสดีครับทุกคน! วันนี้มีสินค้าดีๆ มาแนะนำให้เพื่อนๆ ครับ สินค้าที่มีคุณภาพดี ราคาย่อมเยา และคุ้มค่าการใช้งานอย่างแน่นอน! คุณสมบัติเด่นที่โดดเด่นจริงๆ ใช้งานง่าย สะดวกสบาย เหมาะสำหรับทุกคนในครอบครัว ราคาดีแบบนี้ไม่ควรพลาดนะครับ!",
                "call_to_action": "สั่งซื้อได้เลยครับ อย่าลังเล!",
                "estimated_duration": 45,
                "target_emotion": "friendly",
                "key_points": ["คุณภาพดี", "ราคาคุ้มค่า", "ใช้งานง่าย"]
            },
            {
                "title": f"สคริปต์เน้นคุณภาพ (เวอร์ชั่น {variation_number})",
                "content": "เพื่อนๆ ครับ ถ้าคุณกำลังมองหาสินค้าคุณภาพดี ที่ใช้งานได้จริง ไม่ใช่ของเล่นๆ วันนี้เราขอแนะนำสินค้าพิเศษ ที่ผ่านการคัดสรรมาอย่างดี มีมาตรฐานสูง ทนทาน ใช้งานได้ยาวนาน สำหรับผู้ที่ต้องการของดีจริงๆ ราคานี้ถือว่าคุ้มมากแล้วครับ!",
                "call_to_action": "เชิญสั่งซื้อได้เลยครับ!",
                "estimated_duration": 50,
                "target_emotion": "confident",
                "key_points": ["มาตรฐานสูง", "ทนทาน", "คุ้มค่า"]
            },
            {
                "title": f"สคริปต์สร้างความเร่งด่วน (เวอร์ชั่น {variation_number})",
                "content": "ด่วนครับเพื่อนๆ! โอกาสทองที่ไม่ควรพลาด สินค้าดีๆ ราคาพิเศษ ในช่วงเวลาจำกัดนี้เท่านั้น! ปกติราคาแพงกว่านี้มาก แต่วันนี้เราให้ราคาพิเศษ เพื่อนๆ จะได้ประโยชน์สูงสุด อย่ารอช้าเลยนะครับ เพราะของดีๆ แบบนี้ หมดแล้วหยิบยาก!",
                "call_to_action": "รีบสั่งเลย อย่าให้เสียโอกาส!",
                "estimated_duration": 55,
                "target_emotion": "urgent",
                "key_points": ["ราคาพิเศษ", "เวลาจำกัด", "โอกาสทอง"]
            }
        ]
        
        # Select based on variation number
        script_index = (variation_number - 1) % len(fallback_scripts)
        fallback = fallback_scripts[script_index].copy()
        
        print(f"🔄 Using fallback script: {fallback['title']}")
        return fallback
    
    async def _generate_with_simulation(
        self,
        db: Session,
        product: Product,
        persona: ScriptPersona,
        mood: str,
        count: int,
        custom_instructions: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Generate scripts using simulation when OpenAI is not available"""
        
        print("🎭 Using simulation mode (OpenAI not available)")
        
        generated_scripts = []
        
        for i in range(count):
            script_data = self._simulate_script_generation(product, persona, mood, i + 1)
            
            if script_data:
                # Parse the JSON string
                try:
                    if isinstance(script_data, str):
                        script_data = json.loads(script_data)
                except:
                    pass
                
                # Save to database
                script = self._save_script_to_db(
                    db=db,
                    product=product,
                    persona=persona,
                    script_data=script_data,
                    mood=mood
                )
                
                generated_scripts.append(script.to_dict())
        
        return generated_scripts
    
    def _simulate_script_generation(
        self, 
        product: Product, 
        persona: ScriptPersona, 
        mood: str, 
        variation_number: int
    ) -> Dict[str, Any]:
        """Enhanced simulation with better Thai content"""
        
        # Determine emotion
        emotion = mood if mood != "auto" else getattr(persona, 'default_emotion', 'professional')
        
        # Create variations
        variations = {
            1: {"focus": "คุณสมบัติ", "style": "เนื้อหาครบถ้วน", "energy": "กระตือรือร้น"},
            2: {"focus": "ราคาคุ้มค่า", "style": "เปรียบเทียบราคา", "energy": "เป็นมิตร"},
            3: {"focus": "การใช้งาน", "style": "ประสบการณ์จริง", "energy": "เชื่อถือได้"}
        }
        
        var = variations.get(variation_number, variations[1])
        
        # Build content based on product data
        greeting = self._get_greeting_by_emotion(emotion)
        intro = f"วันนี้ขอแนะนำ {product.name} สินค้าคุณภาพจาก{product.brand or 'แบรนด์ชั้นนำ'}"
        
        # Features section
        features = product.key_features or ["คุณภาพดี", "ใช้งานง่าย", "ทนทาน"]
        features_text = "คุณสมบัติเด่น: " + ", ".join(features[:3])
        
        # Price section
        price_text = f"ราคาเพียง {product.price:,.0f} บาท"
        if hasattr(product, 'is_on_sale') and product.is_on_sale:
            original_price = getattr(product, 'original_price', product.price * 1.2)
            price_text = f"ราคาพิเศษเพียง {float(product.price):,.0f} บาท จากราคาปกติ {float(original_price):,.0f} บาท"
        
        # Closing
        closing = self._get_closing_by_emotion(emotion)
        cta = self._generate_cta(product, emotion)
        
        content = f"{greeting} {intro} {features_text} {price_text} {closing}"
        
        # Estimate duration
        word_count = len(content.split())
        duration = max(30, int(word_count / 2.5))
        
        return {
            "title": f"{product.name} - {var['style']} (สคริปต์ที่ {variation_number})",
            "content": content.strip(),
            "call_to_action": cta,
            "estimated_duration": duration,
            "target_emotion": emotion,
            "key_points": [
                f"เน้น{var['focus']}",
                f"อารมณ์{emotion}",
                f"ระยะเวลา ~{duration} วินาที"
            ]
        }
    
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
    
    def _get_closing_by_emotion(self, emotion: str) -> str:
        """Get appropriate closing based on emotion"""
        closings = {
            "excited": "อย่าลังเลนะครับ! โอกาสดีๆ แบบนี้ไม่มีบ่อย! 🎯",
            "professional": "ขอเชิญสั่งซื้อได้เลยครับ เราพร้อมให้บริการด้วยความใส่ใจ",
            "friendly": "ถ้าสนใจสามารถสั่งได้เลยนะครับ รับรองว่าคุ้มค่าแน่นอน 😊",
            "confident": "เราเชื่อมั่นว่าคุณจะพอใจ สั่งซื้อได้เลยครับ!",
            "energetic": "มาสิครับ! พลาดแล้วเสียดายแน่! ⚡",
            "calm": "สนใจสามารถสั่งซื้อได้ครับ ขอบคุณที่รับฟังครับ",
            "urgent": "รีบสั่งก่อนที่จะหมดนะครับ! เหลือไม่เยอะแล้ว! ⏰"
        }
        return closings.get(emotion, closings["professional"])
    
    def _add_emotional_markup(self, content: str, mood: str, persona: ScriptPersona) -> str:
        """Add emotional markup tags for TTS processing"""
        
        # Determine target emotion
        target_emotion = mood if mood != "auto" else getattr(persona, 'default_emotion', 'professional')
        
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
            tone=persona.speaking_style if hasattr(persona, 'speaking_style') else "professional",
            call_to_action=script_data.get("call_to_action", ""),
            duration_estimate=duration_estimate,
            generation_model=self.settings.OPENAI_MODEL,
            generation_temperature=self.settings.OPENAI_TEMPERATURE,
            generation_prompt=f"Generated with persona: {persona.name}, mood: {mood}",
            status="draft",  # ใช้ enum แทน string
            has_mp3=False,  # เพิ่มให้ชัดเจน
            is_editable=True  # เพิ่มให้ชัดเจน
        )
        
        db.add(script)
        db.commit()  # Commit ทันทีหลังจาก add
        db.refresh(script)  # Refresh เพื่อให้ได้ข้อมูลล่าสุด
        
        return script
    
    async def test_openai_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection and return status"""
        
        if not self.client:
            return {
                "status": "disconnected",
                "message": "OpenAI client not initialized",
                "details": "Check OPENAI_API_KEY in environment variables"
            }
        
        try:
            # Test with a simple request
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=10,
                temperature=0.1
            )
            
            return {
                "status": "connected",
                "message": "OpenAI API connection successful",
                "model": self.settings.OPENAI_MODEL,
                "test_response": response.choices[0].message.content[:50] + "..." if response.choices[0].message.content else "No content"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"OpenAI API connection failed: {str(e)}",
                "details": "Please check your API key and internet connection"
            }


# Global service instance
try:
    ai_script_service = AIScriptService()
    print("✅ AI Script Service initialized successfully")
    print(f"🔧 OpenAI Status: {'Available' if ai_script_service.client else 'Not Available (will use simulation)'}")
except Exception as e:
    print(f"⚠️ AI Script Service initialization failed: {e}")
    ai_script_service = None