# app/services/ai_script_service.py
"""
AI-powered script generation service using ChatGPT
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import json
import random

from app.models.product import Product

class AIScriptService:
    """AI Script Generation Service using ChatGPT"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ OPENAI_API_KEY not found, using fallback templates")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
            print("✅ OpenAI client initialized")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for ChatGPT"""
        return """คุณเป็นผู้เชี่ยวชาญด้านการเขียนสคริปต์การขายสินค้าออนไลน์และ Live Commerce ที่มีประสบการณ์สูง

หน้าที่ของคุณ:
- เขียนสคริปต์การขายที่น่าสนใจและโน้มน้าวใจ
- ใช้ภาษาไทยที่เป็นธรรมชาติและเข้าใจง่าย
- สร้างอารมณ์และความรู้สึกที่เหมาะสมกับแต่ละแบบ
- ใช้เทคนิคการขายที่ได้ผลจริง
- ความยาวประมาณ 80-120 คำ

กฎการเขียน:
- ใช้ภาษาสุภาพแต่เป็นมิตร
- ไม่ใช้คำหยาบหรือไม่เหมาะสม
- สร้างความน่าเชื่อถือ
- เน้นประโยชน์ของลูกค้า
- ใช้ emoji ได้บ้างแต่อย่าบ่อยเกินไป"""

    def _get_script_prompts(self, product: Product) -> List[Dict[str, str]]:
        """Get prompts for different script types"""
        
        price_text = f"{product.price:,.0f}"
        
        prompts = [
            {
                "type": "emotional",
                "title": "แบบกระตุ้นความต้องการ",
                "prompt": f"""สร้างสคริปต์การขายแบบกระตุ้นความต้องการและเร่งด่วนสำหรับ:
                
สินค้า: {product.name}
ราคา: {price_text} บาท
คำอธิบาย: {product.description}
สต็อก: {product.stock} ชิ้น
หมวดหมู่: {product.category}

ต้องการสคริปต์ที่:
- สร้างความรู้สึกเร่งด่วน (FOMO)
- เน้นความพิเศษและหายาก
- ใช้คำที่กระตุ้นอารมณ์
- มีการเรียกปฏิสัมพันธ์
- เน้นข้อจำกัดเวลาหรือสต็อก"""
            },
            {
                "type": "informative", 
                "title": "แบบให้ข้อมูลละเอียด",
                "prompt": f"""สร้างสคริปต์การขายแบบให้ข้อมูลสำหรับ:

สินค้า: {product.name}
ราคา: {price_text} บาท  
คำอธิบาย: {product.description}
สต็อก: {product.stock} ชิ้น
หมวดหมู่: {product.category}

ต้องการสคริปต์ที่:
- เน้นข้อมูลและรายละเอียดสินค้า
- อธิบายประโยชน์และคุณสมบัติ
- เปรียบเทียบคุณภาพกับราคา
- สร้างความน่าเชื่อถือ
- ใช้ข้อมูลเป็นหลักในการโน้มน้าว"""
            },
            {
                "type": "interactive",
                "title": "แบบสร้างปฏิสัมพันธ์", 
                "prompt": f"""สร้างสคริปต์การขายแบบโต้ตอบสำหรับ:

สินค้า: {product.name}
ราคา: {price_text} บาท
คำอธิบาย: {product.description} 
สต็อก: {product.stock} ชิ้น
หมวดหมู่: {product.category}

ต้องการสคริปต์ที่:
- เรียกร้องให้คนดูมีส่วนร่วม
- ถามคำถามและขอความคิดเห็น
- สร้างบรรยากาศสนุกสนาน
- ใช้ภาษาเป็นกันเองและเข้าถึงง่าย
- มีการเรียกให้พิมพ์แชทหรือตอบสนอง"""
            }
        ]
        
        return prompts

    async def generate_ai_scripts(self, product: Product) -> List[Dict[str, str]]:
        """Generate 3 AI-powered scripts for a product"""
        
        if not self.client:
            print("⚠️ OpenAI not available, using fallback")
            return self._get_fallback_scripts(product)
        
        try:
            prompts = self._get_script_prompts(product)
            scripts = []
            
            system_prompt = self._get_system_prompt()
            
            # Generate each script type
            for prompt_data in prompts:
                print(f"🤖 Generating {prompt_data['title']}...")
                
                response = await self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # หรือ "gpt-4" ถ้าต้องการคุณภาพสูงกว่า
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt_data['prompt']}
                    ],
                    max_tokens=300,
                    temperature=0.8,  # ความคิดสร้างสรรค์สูงหน่อย
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                
                script_content = response.choices[0].message.content.strip()
                
                scripts.append({
                    "title": prompt_data["title"],
                    "content": script_content,
                    "script_type": prompt_data["type"]
                })
                
                print(f"✅ Generated {prompt_data['title']}")
                
                # เว้นระยะเพื่อไม่ให้ hit rate limit
                await asyncio.sleep(0.5)
            
            print(f"🎉 Generated {len(scripts)} AI scripts for {product.name}")
            return scripts
            
        except Exception as e:
            print(f"❌ AI script generation failed: {e}")
            print("🔄 Falling back to template scripts...")
            return self._get_fallback_scripts(product)
    
    def _get_fallback_scripts(self, product: Product) -> List[Dict[str, str]]:
        """Fallback template scripts when AI is not available"""
        
        price_text = f"{product.price:,.0f}"
        
        # ปรับปรุง template ให้หลากหลายกว่าเดิม
        emotional_variations = [
            f"สวัสดีครับทุกคน! วันนี้มีโปรโมชั่นสุดพิเศษ {product.name} มาแนะนำ! {product.description} ราคาเพียง {price_text} บาทเท่านั้น! โอกาสนี้หาได้ยากมาก รีบสั่งก่อนหมดนะครับ! 🔥",
            f"เฮ้ย! ใครที่รออยู่ ถึงเวลาแล้วนะ! {product.name} สุดฮิต {product.description} ลดพิเศษเหลือ {price_text} บาท! ของดีแบบนี้หายากมากๆ ไม่รีบไม่ทันแน่! 🔥",
            f"พิเศษสุดๆ วันนี้เท่านั้น! {product.name} {product.description} โปรเจ็บเพียง {price_text} บาท! สต็อกมีจำกัดเพียง {product.stock} ชิ้น ใครเร็วได้ก่อน! 💥"
        ]
        
        informative_variations = [
            f"ขอแนะนำ {product.name} ครับ {product.description} ในราคาที่คุ้มค่าที่สุด {price_text} บาท หมวดหมู่ {product.category} คุณภาพระดับพรีเมียม สต็อกมีจำกัด {product.stock} ชิ้น",
            f"มาดูสินค้าคุณภาพกันครับ {product.name} {product.description} ราคาเพียง {price_text} บาท คุ้มค่าสุดๆ ในหมวด {product.category} สินค้าแท้ 100% รับประกันคุณภาพ",
            f"สินค้าดีราคาดี {product.name} {product.description} เพียง {price_text} บาท เท่านั้น! หมวดหมู่ {product.category} ที่ขายดีที่สุด มีให้เลือกจำนวนจำกัด {product.stock} ชิ้น"
        ]
        
        interactive_variations = [
            f"เฮ้ยทุกคน! ใครกำลังมองหา {product.name} บ้าง? 🙋‍♀️ {product.description} ราคาดีสุดๆ {price_text} บาท! พิมพ์ 'สนใจ' ให้ดูหน่อย! ใครเร็วได้โปรพิเศษ! 💝",
            f"คืนนี้มีของดีมาโชว์! {product.name} {product.description} ราคาเพียง {price_text} บาท! ใครชอบพิมพ์ ❤️ ใน chat นะครับ! คนแรกได้ส่วนลดเพิ่ม! 🎁",
            f"ทุกคนพร้อมแล้วไหม? {product.name} {product.description} โปรพิเศษ {price_text} บาท! ใครอยากได้กดไลค์ให้ดูหน่อย! มีเพียง {product.stock} ชิ้นเท่านั้น! 🎉"
        ]
        
        return [
            {
                "title": "แบบกระตุ้นความต้องการ",
                "content": random.choice(emotional_variations),
                "script_type": "emotional"
            },
            {
                "title": "แบบให้ข้อมูลละเอียด", 
                "content": random.choice(informative_variations),
                "script_type": "informative"
            },
            {
                "title": "แบบสร้างปฏิสัมพันธ์",
                "content": random.choice(interactive_variations),
                "script_type": "interactive"
            }
        ]
    
    async def generate_custom_script(
        self,
        product: Product,
        style: str = "friendly",
        focus: str = "benefits",
        length: str = "medium"
    ) -> str:
        """Generate a custom script with specific parameters"""
        
        if not self.client:
            return self._get_fallback_scripts(product)[0]["content"]
        
        try:
            custom_prompt = f"""สร้างสคริปต์การขายสำหรับ:
            
สินค้า: {product.name}
ราคา: {product.price:,.0f} บาท
คำอธิบาย: {product.description}

สไตล์: {style}
เน้น: {focus}  
ความยาว: {length}

สร้างสคริปต์ที่เหมาะสมตามพารามิเตอร์ที่กำหนด"""

            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": custom_prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ Custom script generation failed: {e}")
            return self._get_fallback_scripts(product)[0]["content"]

# Global AI script service instance
ai_script_service = AIScriptService()

# สำหรับ import ที่ต้องการ class
__all__ = ['AIScriptService', 'ai_script_service']