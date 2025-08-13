#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, SessionLocal, create_tables
from app.models.product import Product, ProductStatus
from app.models.script import Script, ScriptPersona, VoicePersona, ScriptType, GenderType
from app.models.user import User
from app.core.security import SecurityManager

def create_sample_personas(db: Session):
    print("\n👤 Creating sample personas...")
    
    script_personas = [
        {
            "name": "Energetic Seller",
            "description": "เซลส์มันส์ที่มีพลังและความกระตือรือร้นสูง",
            "personality_traits": ["enthusiastic", "confident", "persuasive"],
            "speaking_style": "พูดเร็ว เต็มไปด้วยพลัง",
            "target_audience": "วัยรุ่น ผู้ซื้อแบบ impulse buy",
            "system_prompt": "คุณเป็นเซลส์มันส์ที่มีพลังสูง พูดด้วยความตื่นเต้น",
            "sample_phrases": ["สุดยอดมากครับ!", "เจ๋งจริงๆ เลย!"],
            "tone_guidelines": "ใช้น้ำเสียงที่มีพลัง",
            "do_say": ["สุดยอด", "เจ๋งมาก"],
            "dont_say": ["อาจจะ", "ไม่แน่ใจ"],
            "default_emotion": "excited",
            "available_emotions": ["excited", "energetic"],
            "sort_order": 1
        }
    ]
    
    # ส่วนที่มีอยู่แล้วของคุณจะอยู่ตรงนี้

    for persona_data in script_personas:
        persona = ScriptPersona(**persona_data)
        db.add(persona)
    
    # Voice Personas
    voice_personas = [
        {
            "name": "Professional Female",
            "description": "เสียงหญิงมืออาชีพ เหมาะสำหรับการนำเสนอธุรกิจ",
            "tts_provider": "edge",
            "voice_id": "th-TH-PremwadeeNeural",
            "language": "th",
            "gender": GenderType.FEMALE,
            "age_range": "adult",
            "accent": "thai_central",
            "speed": 0.9,
            "pitch": 1.0,
            "volume": 1.0,
            "emotion": "professional",
            "emotional_range": ["professional", "confident", "calm"],
            "provider_settings": {"style": "general"},
            "quality_rating": 5,
            "is_active": True
        },
        {
            "name": "Energetic Male",
            "description": "เสียงชายร่าเริง เหมาะสำหรับการขายแบบมีพลัง",
            "tts_provider": "edge",
            "voice_id": "th-TH-NiwatNeural",
            "language": "th",
            "gender": GenderType.MALE,
            "age_range": "young",
            "accent": "thai_central",
            "speed": 1.1,
            "pitch": 1.1,
            "volume": 1.0,
            "emotion": "energetic",
            "emotional_range": ["energetic", "excited", "confident"],
            "provider_settings": {"style": "cheerful"},
            "quality_rating": 4,
            "is_active": True
        },
        {
            "name": "Gentle Female",
            "description": "เสียงหญิงอ่อนโยน เหมาะสำหรับสินค้าไลฟ์สไตล์",
            "tts_provider": "google",
            "voice_id": "th",
            "language": "th",
            "gender": GenderType.FEMALE,
            "age_range": "adult",
            "accent": "thai_central",
            "speed": 0.8,
            "pitch": 0.9,
            "volume": 1.0,
            "emotion": "gentle",
            "emotional_range": ["gentle", "warm", "caring"],
            "provider_settings": {},
            "quality_rating": 3,
            "is_active": True
        },
        {
            "name": "Dynamic Male",
            "description": "เสียงชายมีพลัง เหมาะสำหรับสินค้าเทคโนโลยี",
            "tts_provider": "edge",
            "voice_id": "th-TH-NiwatNeural",
            "language": "th",
            "gender": GenderType.MALE,
            "age_range": "adult",
            "accent": "thai_central",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
            "emotion": "dynamic",
            "emotional_range": ["dynamic", "confident", "professional"],
            "provider_settings": {"style": "newscast"},
            "quality_rating": 4,
            "is_active": True
        }
    ]
    
    for voice_data in voice_personas:
        voice = VoicePersona(**voice_data)
        db.add(voice)
    
    print(f"✅ Created {len(script_personas)} script personas and {len(voice_personas)} voice personas")

def create_sample_products(db: Session):
    """Create sample products with detailed information for AI script generation"""
    print("\n📦 Creating sample products...")
    
    products = [
        {
            "sku": "CAM-AI-4K-001",
            "name": "AI Smart Camera Pro 4K",
            "description": "กล้องอัจฉริยะ 4K พร้อมระบบ AI สำหรับรักษาความปลอดภัยบ้าน ตรวจจับการเคลื่อนไหวอัตโนมัติ บันทึกภาพคมชัดทั้งกลางวันและกลางคืน",
            "price": 2999.00,
            "original_price": 3999.00,
            "discount_percentage": 25,
            "category": "electronics",
            "brand": "SmartHome Pro",
            "stock_quantity": 50,
            "key_features": [
                "ความละเอียด 4K Ultra HD",
                "ระบบ AI ตรวจจับการเคลื่อนไหว",
                "Night Vision ชัดแม้ในที่มืด",
                "แจ้งเตือนผ่าน Smartphone",
                "บันทึกภาพลง Cloud Storage",
                "กันน้ำ IP65",
                "ติดตั้งง่าย ไร้สาย WiFi"
            ],
            "selling_points": [
                "ประหยัดไฟ 70% เทียบรุ่นเก่า",
                "รับประกัน 2 ปีเต็ม",
                "ส่งฟรีทั่วประเทศ",
                "ติดตั้งให้ฟรีในกรุงเทพ",
                "รีวิวดี 4.8/5 ดาว"
            ],
            "target_audience": "เจ้าของบ้าน นักธุรกิจ ผู้ที่ห่วงความปลอดภัย",
            "use_cases": [
                "รักษาความปลอดภัยบ้าน",
                "เฝ้าระวังร้านค้า",
                "ดูแลผู้สูงอายุ",
                "เฝ้าระวังสัตว์เลี้ยง"
            ],
            "promotion_text": "🔥 Flash Sale! ลด 25% เหลือเพียง 2,999 บาท (จากราคา 3,999 บาท) วันนี้เท่านั้น! พร้อมของแถมมูลค่า 500 บาท",
            "warranty_info": "รับประกันสินค้า 2 ปี พร้อมบริการซ่อมฟรี",
            "shipping_info": "ส่งฟรีทั่วประเทศ ได้รับภายใน 1-2 วัน",
            "tags": ["camera", "security", "AI", "4K", "smart-home"],
            "status": ProductStatus.ACTIVE
        },
        {
            "sku": "EAR-WL-PRO-002",
            "name": "Wireless Earbuds Elite Pro",
            "description": "หูฟังไร้สาย Premium พร้อมระบบตัดเสียงรบกวน Active Noise Cancelling คุณภาพเสียง Hi-Fi และแบตเตอรี่ทนนาน 8 ชั่วโมง",
            "price": 1599.00,
            "original_price": 2299.00,
            "discount_percentage": 30,
            "category": "electronics",
            "brand": "AudioTech Elite",
            "stock_quantity": 75,
            "key_features": [
                "Active Noise Cancelling (ANC)",
                "คุณภาพเสียง Hi-Fi Premium",
                "แบตเตอรี่ 8 ชั่วโมง + เคส 24 ชั่วโมง",
                "กันน้ำ IPX7",
                "Quick Charge 15 นาที = 2 ชั่วโมง",
                "Touch Control สะดวก",
                "เชื่อมต่อ Bluetooth 5.3"
            ],
            "selling_points": [
                "เสียงเบสหนักแบบ Studio",
                "ใส่สบาย ไม่หลุด",
                "รองรับ iOS และ Android",
                "มีแอพควบคุมเสียง",
                "รีวิวจากดารา นักร้อง"
            ],
            "target_audience": "นักฟังเพลง นักกีฬา คนทำงาน Gen Y-Z",
            "use_cases": [
                "ฟังเพลงคุณภาพสูง",
                "ออกกำลังกาย",
                "Work from Home",
                "เรียน Online",
                "เดินทาง"
            ],
            "promotion_text": "💥 Super Sale! หูฟังระดับ Pro ลดราคาพิเศษ 30% เหลือ 1,599 บาท แถมฟรี เคสหนัง Premium มูลค่า 399 บาท!",
            "status": ProductStatus.ACTIVE
        },
        {
            "sku": "HUB-SM-CTRL-003",
            "name": "Smart Home Hub Central",
            "description": "ศูนย์ควบคุมบ้านอัจฉริยะรุ่นใหม่ เชื่อมต่ออุปกรณ์ IoT ได้หลากหลาย ควบคุมผ่านเสียงและแอพ ประหยัดไฟอัตโนมัติ",
            "price": 3999.00,
            "category": "electronics",
            "brand": "SmartLife Tech",
            "stock_quantity": 30,
            "key_features": [
                "รองรับอุปกรณ์ 50+ ชิ้น",
                "ควบคุมด้วยเสียง (Voice Control)",
                "ตั้งเวลาอัตโนมัติ",
                "ประหยัดไฟ 40%",
                "รองรับ Alexa, Google Assistant",
                "แอพ SmartLife ใช้ง่าย",
                "ระบบรักษาความปลอดภัยขั้นสูง"
            ],
            "selling_points": [
                "ติดตั้งง่าย 10 นาที",
                "ประหยัดค่าไฟ 2,000 บาท/ปี",
                "อัพเดท Feature ฟรีตลอดชีวิต",
                "รองรับ Smart Device ทุกยี่ห้อ"
            ],
            "target_audience": "เจ้าของบ้าน คนรักเทคโนโลยี ครอบครัวยุคใหม่",
            "status": ProductStatus.ACTIVE
        },
        {
            "sku": "KEY-GME-RGB-004",
            "name": "Gaming Mechanical Keyboard RGB",
            "description": "คีย์บอร์ดเกมมิ่งระดับโปร สวิตช์ Mechanical แท้ ไฟ RGB แบบ Custom พร้อม Macro Keys และ Anti-Ghosting เต็มรูปแบบ",
            "price": 2599.00,
            "category": "electronics",
            "brand": "GamePro Elite",
            "stock_quantity": 40,
            "key_features": [
                "สวิตช์ Mechanical Cherry MX Blue",
                "ไฟ RGB 16.8 ล้านสี",
                "Anti-Ghosting เต็มรูปแบบ",
                "Macro Keys 12 ปุ่ม",
                "โครงอลูมิเนียมแข็งแรง",
                "ปุ่ม Multimedia พิเศษ",
                "Cable ถอดได้"
            ],
            "selling_points": [
                "ใช้ได้ทั้ง Gaming และ Office",
                "เสียงการพิมพ์นุ่มหู",
                "รับประกัน 3 ปี",
                "รีวิวดีจาก Pro Gamer"
            ],
            "target_audience": "นักเล่นเกม โปรแกรมเมอร์ คนทำงานที่ใช้คอมนาน",
            "status": ProductStatus.ACTIVE
        },
        {
            "sku": "SSD-PORT-1TB-005",
            "name": "Portable SSD External 1TB",
            "description": "SSD พกพาความเร็วสูง 1TB อ่านเขียนเร็วกว่า HDD ธรรมดา 10 เท่า ขนาดเล็ก เบา กันกระแทก เหมาะสำหรับงานกราฟิก วิดีโอ",
            "price": 3499.00,
            "category": "electronics",
            "brand": "SpeedDrive Pro",
            "stock_quantity": 60,
            "key_features": [
                "ความจุ 1TB (1,000 GB)",
                "ความเร็วอ่าน 1,000 MB/s",
                "ขนาดเล็ก 10x5x1 ซม.",
                "น้ำหนักเบา 150 กรัม",
                "กันกระแทก Military Grade",
                "รองรับ USB-C และ USB-A",
                "ใช้ได้ทั้ง Mac และ PC"
            ],
            "selling_points": [
                "เร็วกว่า HDD ธรรมดา 10 เท่า",
                "ประหยัดพื้นที่ 90%",
                "ไม่มีเสียงรบกวน",
                "ประหยัดไฟ 70%"
            ],
            "target_audience": "นักออกแบบ โปรแกรมเมอร์ ช่างภาพ คนทำวิดีโอ",
            "status": ProductStatus.ACTIVE
        },
        {
            "sku": "CHG-WL-STAND-006",
            "name": "Wireless Charging Stand Pro",
            "description": "แท่นชาร์จไร้สายแบบตั้ง รองรับ Fast Charging 15W พร้อมพัดลมระบายความร้อนในตัว ชาร์จได้ทั้งแนวตั้งและแนวนอน",
            "price": 899.00,
            "original_price": 1299.00,
            "discount_percentage": 31,
            "category": "electronics",
            "brand": "ChargeTech Pro",
            "stock_quantity": 80,
            "key_features": [
                "Fast Charging 15W",
                "รองรับ iPhone และ Samsung",
                "พัดลมระบายความร้อนอัตโนมัติ",
                "ชาร์จได้ 2 ท่า (ตั้ง/นอน)",
                "ไฟ LED แสดงสถานะ",
                "ระบบป้องกันไฟเกิน",
                "โครงอลูมิเนียมแข็งแรง"
            ],
            "selling_points": [
                "ชาร์จเร็วกว่าสาย USB ธรรมดา",
                "ปลอดภัย 100% ไม่ไฟไหม้",
                "ใช้ขณะดูหนัง Video Call ได้",
                "ประหยัดสายชาร์จ"
            ],
            "target_audience": "คนทำงาน สาย Gadget ผู้ใช้ Smartphone รุ่นใหม่",
            "promotion_text": "🎁 ลดพิเศษ 31% เหลือ 899 บาท พร้อมแถมสายชาร์จ Type-C ฟรี! จำนวนจำกัด",
            "status": ProductStatus.ACTIVE
        }
    ]
    
    for product_data in products:
        product = Product(**product_data)
        db.add(product)
    
    print(f"✅ Created {len(products)} sample products")

def create_sample_user(db: Session):
    """Create demo user"""
    print("\n👤 Creating demo user...")
    
    # Check if demo user already exists
    existing_user = db.query(User).filter(User.email == "demo@example.com").first()
    if existing_user:
        print("ℹ️ Demo user already exists")
        return
    
    demo_user = User(
        email="demo@example.com",
        username="demo",
        hashed_password=SecurityManager.get_password_hash("demo123"),
        full_name="Demo User",
        is_active=True,
        is_superuser=False,
        preferences={
            "theme": "light",
            "language": "th",
            "notifications": True
        }
    )
    
    db.add(demo_user)
    print("✅ Created demo user:")
    print("   📧 Email: demo@example.com")
    print("   👤 Username: demo")
    print("   🔑 Password: demo123")

def create_sample_scripts(db: Session):
    """Create sample scripts for some products"""
    print("\n📝 Creating sample scripts...")
    
    # Get first 3 products and personas
    products = db.query(Product).limit(3).all()
    personas = db.query(ScriptPersona).all()
    
    if not products or not personas:
        print("⚠️ No products or personas found, skipping scripts")
        return
    
    sample_scripts = []
    
    # Script for AI Smart Camera
    if len(products) > 0:
        camera_scripts = [
            {
                "product_id": products[0].id,
                "persona_id": personas[0].id if personas else None,
                "title": "AI Smart Camera - Energetic Introduction",
                "content": """{excited}สวัสดีครับทุกคน! วันนี้มีข่าวดีมาแชร์กันครับ!{/excited} 

{confident}ขอแนะนำ AI Smart Camera Pro 4K กล้องอัจฉริยะที่จะเปลี่ยนบ้านของคุณให้เป็น Smart Home แบบมืออาชีพ!{/confident}

🌟 ไฮไลท์พิเศษ:
• {excited}ความละเอียด 4K Ultra HD ชัดแบบโครตแตก!{/excited}
• ระบบ AI ตรวจจับการเคลื่อนไหวอัตโนมัติ แจ้งเตือนทันที
• {confident}Night Vision ชัดแม้ในที่มืดมิด เหมือนมีไฟเปิด{/confident}
• กันน้ำ IP65 ฝนตกลายฟ้าผ่าก็ไม่กลัว!

{urgent}🔥 Flash Sale วันนี้เท่านั้น! ลดราคาพิเศษ 25% จาก 3,999 เหลือเพียง 2,999 บาท พร้อมของแถมมูลค่า 500 บาท!{/urgent}

{excited}รีบสั่งเลยครับ! เหลือไม่เยอะแล้ว ไม่สั่งเสียดายแน่นอน! 🛒{/excited}""",
                "script_type": ScriptType.AI_GENERATED,
                "target_emotion": "excited",
                "call_to_action": "สั่งเลยครับ! ไม่สั่งเสียดาย! 🛒",
                "duration_estimate": 75
            }
        ]
        sample_scripts.extend(camera_scripts)
    
    # Script for Wireless Earbuds
    if len(products) > 1:
        earbuds_scripts = [
            {
                "product_id": products[1].id,
                "persona_id": personas[1].id if len(personas) > 1 else personas[0].id,
                "title": "Wireless Earbuds - Professional Review",
                "content": """{professional}สวัสดีครับ ยินดีต้อนรับทุกท่านสู่การนำเสนอสินค้าพิเศษ{/professional}

{confident}ในฐานะผู้เชี่ยวชาญด้านเทคโนโลยีเสียง วันนี้ขอแนะนำ Wireless Earbuds Elite Pro หูฟังไร้สายระดับ Premium ที่จะเปลี่ยนประสบการณ์การฟังเพลงของคุณ{/confident}

🎵 คุณสมบัติโดดเด่น:
• {trustworthy}Active Noise Cancelling ตัดเสียงรบกวนได้ 95%{/trustworthy}
• คุณภาพเสียง Hi-Fi เทียบเท่าสตูดิโอระดับมืออาชีพ
• แบตเตอรี่ยาวนาน 8+24 ชั่วโมง ใช้ได้ทั้งวัน
• {professional}กันน้ำ IPX7 ใส่ออกกำลังกายได้อย่างมั่นใจ{/professional}

{confident}ประสบการณ์จากการทดสอบ: เสียงเบสหนัก treble ใส ไม่บิดเบือน เหมาะสำหรับทุกแนวเพลง{/confident}

💰 ราคาพิเศษ: จาก 2,299 บาท ลดเหลือ 1,599 บาท ประหยัด 700 บาท พร้อมเคสหนัง Premium ฟรี!

{professional}สั่งซื้อได้ทันทีครับ รับรองคุณภาพระดับสากล{/professional}""",
                "script_type": ScriptType.AI_GENERATED,
                "target_emotion": "professional",
                "call_to_action": "สั่งซื้อได้ทันทีครับ รับรองคุณภาพระดับสากล",
                "duration_estimate": 85
            }
        ]
        sample_scripts.extend(earbuds_scripts)
    
    # Script for Smart Home Hub  
    if len(products) > 2:
        hub_scripts = [
            {
                "product_id": products[2].id,
                "persona_id": personas[2].id if len(personas) > 2 else personas[0].id,
                "title": "Smart Home Hub - Friendly Recommendation",
                "content": """{friendly}สวัสดีครับเพื่อนๆ มาเจอกันอีกแล้วนะครับ 😊{/friendly}

{warm}วันนี้อยากแชร์สินค้าที่ช่วยให้บ้านผมสะดวกขึ้นมากเลย Smart Home Hub Central ศูนย์ควบคุมบ้านอัจฉริยะที่ใช้ง่ายจริงๆ{/warm}

{honest}บอกตามตรงนะครับ ตอนแรกก็ไม่เชื่อหรอกว่าจะดีขนาดนั้น แต่ลองใช้ดูแล้วติดใจเลย!{/honest}

✨ สิ่งที่ผมชอบมากๆ:
• ควบคุมไฟ แอร์ ทีวี ด้วยเสียงพูด "เปิดไฟห้องนอน" ก็เปิดเลย
• {caring}ตั้งเวลาให้อุปกรณ์เปิด-ปิดอัตโนมัติ ประหยัดไฟได้จริงๆ{/caring}
• ติดตั้งง่าย 10 นาทีเสร็จ ไม่ต้องเรียกช่าง
• {warm}ลูกๆ ก็ใช้ได้ ผู้ปกครองคุมได้ด้วย{/warm}

💰 ราคา 3,999 บาท คุ้มมากเทียบกับที่ได้ บ้านเป็น Smart Home เต็มๆ

{friendly}ลองดูนะครับ รับรองว่าคุ้มค่าจริงๆ แถมประหยัดค่าไฟด้วย 😊{/friendly}""",
                "script_type": ScriptType.AI_GENERATED,
                "target_emotion": "friendly",
                "call_to_action": "ลองดูนะครับ รับรองว่าคุ้มค่าจริงๆ 😊",
                "duration_estimate": 70
            }
        ]
        sample_scripts.extend(hub_scripts)
    
    # Save scripts to database
    for script_data in sample_scripts:
        script = Script(**script_data)
        db.add(script)
    
    print(f"✅ Created {len(sample_scripts)} sample scripts with emotional markup")

def display_summary(db: Session):
    """Display database summary"""
    print("\n" + "=" * 60)
    print("📊 Database Summary:")
    print("=" * 60)
    
    # Count records
    user_count = db.query(User).count()
    product_count = db.query(Product).count()
    script_count = db.query(Script).count()
    script_persona_count = db.query(ScriptPersona).count()
    voice_persona_count = db.query(VoicePersona).count()
    
    print(f"👥 Users: {user_count}")
    print(f"📦 Products: {product_count}")
    print(f"📝 Scripts: {script_count}")
    print(f"🎭 Script Personas: {script_persona_count}")
    print(f"🎵 Voice Personas: {voice_persona_count}")
    
    # Product details
    active_products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
    print(f"✅ Active Products: {active_products}")
    
    # Featured products
    featured_products = db.query(Product).filter(Product.discount_percentage > 0).count()
    print(f"⭐ Featured Products (On Sale): {featured_products}")
    
    # Total stock
    total_stock = db.query(func.sum(Product.stock_quantity)).scalar() or 0
    print(f"📦 Total Stock: {total_stock} units")
    
    print("\n🎉 Database initialization completed successfully!")
    print("🚀 You can now start the server with: python run_server.py")
    print("📱 Dashboard: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")

def reset_database():
    """Reset database (delete all data)"""
    print("⚠️ DANGER: This will delete ALL data in the database!")
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm != "RESET":
        print("❌ Reset cancelled")
        return False
    
    try:
        print("🗄️ Resetting database...")
        
        # Drop all tables
        from app.models.base import Base
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
        
        # Recreate tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables recreated")
        
        print("✅ Database reset completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database reset failed: {e}")
        return False

def test_connection():
    """Test database connection"""
    try:
        print("🔍 Testing database connection...")
        
        db = SessionLocal()
        
        # Test query
        result = db.execute(text("SELECT 1")).fetchone()
        
        if result:
            print("✅ Database connection successful!")
            
            # Show table info
            tables = db.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)).fetchall()
            
            print(f"📋 Found {len(tables)} tables:")
            for table in tables:
                count = db.execute(text(f"SELECT COUNT(*) FROM {table[0]}")).scalar()
                print(f"   • {table[0]}: {count} records")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def init_database():
    """Initialize database with tables and sample data"""
    print("🗄️ Initializing AI Live Commerce Database...")
    print("=" * 60)
    
    try:
        # Create all tables
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Create sample data
            create_sample_personas(db)
            create_sample_products(db)
            create_sample_user(db)
            create_sample_scripts(db)
            
            db.commit()
            print("✅ All sample data created successfully!")
            
            # Display summary
            display_summary(db)
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True 

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🚀 AI Live Commerce Platform - Database Management")
        print("=" * 60)
        print("Available commands:")
        print("  python main_dashboard_init.py initdb    - Initialize database with sample data")
        print("  python main_dashboard_init.py reset     - Reset database (delete all data)")
        print("  python main_dashboard_init.py test      - Test database connection")
        print("  python main_dashboard_init.py stats     - Show database statistics")
        print("  python main_dashboard_init.py backup    - Backup database")
        print("=" * 60)
        return
    
    command = sys.argv[1].lower()
    
    if command == "initdb":
        success = init_database()
        if success:
            print("\n🎉 Database initialization completed successfully!")
            print("🚀 Next steps:")
            print("   1. Run: python run_server.py")
            print("   2. Visit: http://localhost:8000")
            print("   3. Login: demo@example.com / demo123")
        else:
            print("\n❌ Database initialization failed!")
            sys.exit(1)
            
    elif command == "reset":
        success = reset_database()
        if success:
            print("\n🎉 Database reset completed!")
            print("💡 Run 'python main_dashboard_init.py initdb' to recreate sample data")
        else:
            sys.exit(1)
            
    elif command == "test":
        success = test_connection()
        if not success:
            sys.exit(1)
            
    elif command == "stats":
        show_stats()
        
    elif command == "backup":
        backup_database()
        
    elif command == "createsuperuser":
        create_superuser()
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see available commands")
        sys.exit(1)

def show_stats():
    """Show database statistics"""
    try:
        print("📊 Database Statistics")
        print("=" * 40)
        
        db = SessionLocal()
        
        # Basic counts
        user_count = db.query(User).count()
        product_count = db.query(Product).count()
        script_count = db.query(Script).count()
        mp3_count = db.query(MP3File).count() if 'MP3File' in globals() else 0
        script_persona_count = db.query(ScriptPersona).count()
        voice_persona_count = db.query(VoicePersona).count()
        
        print(f"👥 Users: {user_count}")
        print(f"📦 Products: {product_count}")
        print(f"📝 Scripts: {script_count}")
        print(f"🎵 MP3 Files: {mp3_count}")
        print(f"🎭 Script Personas: {script_persona_count}")
        print(f"🎤 Voice Personas: {voice_persona_count}")
        
        if product_count > 0:
            print("\n📦 Product Breakdown:")
            active_products = db.query(Product).filter(Product.status == ProductStatus.ACTIVE).count()
            on_sale_products = db.query(Product).filter(Product.discount_percentage > 0).count()
            total_stock = db.query(func.sum(Product.stock_quantity)).scalar() or 0
            
            print(f"   ✅ Active: {active_products}")
            print(f"   🔥 On Sale: {on_sale_products}")
            print(f"   📦 Total Stock: {total_stock} units")
        
        if script_count > 0:
            print("\n📝 Script Breakdown:")
            ai_scripts = db.query(Script).filter(Script.script_type == ScriptType.AI_GENERATED).count()
            manual_scripts = db.query(Script).filter(Script.script_type == ScriptType.MANUAL).count()
            scripts_with_mp3 = db.query(Script).filter(Script.has_mp3 == True).count()
            
            print(f"   🤖 AI Generated: {ai_scripts}")
            print(f"   ✏️ Manual: {manual_scripts}")
            print(f"   🎵 With MP3: {scripts_with_mp3}")
        
        # Database file size
        db_path = "ai_live_commerce.db"
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            size_mb = size_bytes / 1024 / 1024
            print(f"\n💾 Database Size: {size_mb:.2f} MB")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")

def backup_database():
    """Backup database"""
    try:
        import shutil
        from datetime import datetime
        
        source = "ai_live_commerce.db"
        if not os.path.exists(source):
            print("❌ Database file not found")
            return
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"ai_live_commerce_backup_{timestamp}.db"
        
        # Create backups directory
        os.makedirs("backups", exist_ok=True)
        backup_path = f"backups/{backup_name}"
        
        # Copy database
        shutil.copy2(source, backup_path)
        
        # Get file sizes
        source_size = os.path.getsize(source) / 1024 / 1024
        backup_size = os.path.getsize(backup_path) / 1024 / 1024
        
        print(f"✅ Database backed up successfully!")
        print(f"📂 Source: {source} ({source_size:.2f} MB)")
        print(f"💾 Backup: {backup_path} ({backup_size:.2f} MB)")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")

def create_superuser():
    """Create superuser account"""
    try:
        print("👤 Create Superuser Account")
        print("=" * 30)
        
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required")
            return
        
        username = input("Username: ").strip()
        if not username:
            print("❌ Username is required")
            return
        
        password = input("Password: ").strip()
        if not password:
            print("❌ Password is required")
            return
        
        full_name = input("Full Name (optional): ").strip()
        
        db = SessionLocal()
        
        # Check if user exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing:
            print("❌ User with this email or username already exists")
            db.close()
            return
        
        # Create superuser
        superuser = User(
            email=email,
            username=username,
            hashed_password=SecurityManager.get_password_hash(password),
            full_name=full_name or username,
            is_active=True,
            is_superuser=True,
            preferences={"role": "admin"}
        )
        
        db.add(superuser)
        db.commit()
        db.close()
        
        print("✅ Superuser created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Username: {username}")
        print("🔑 You can now login with these credentials")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    main()#!/usr/bin/env python3
"""
Database Initialization for AI Live Commerce Platform
Creates tables, sample data, and default personas
"""

import sys
import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

# Add app directory to path
sys.path.append(str(Path(__file__).parent))

from app.core.database import engine, SessionLocal, create_tables
from app.models.product import Product, ProductStatus
from app.models.script import Script, ScriptPersona, VoicePersona, ScriptType, GenderType
from app.models.user import User
from app.core.security import SecurityManager

def init_database():
    """Initialize database with tables and sample data"""
    print("🗄️ Initializing AI Live Commerce Database...")
    print("=" * 60)
    
    try:
        # Create all tables
        print("📋 Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Create session
        db = SessionLocal()
        
        try:
            # Create sample data
            create_sample_personas(db)
            create_sample_products(db)
            create_sample_user(db)
            create_sample_scripts(db)
            
            db.commit()
            print("✅ All sample data created successfully!")
            
            # Display summary
            display_summary(db)
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            db.rollback()
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

def create_sample_personas(db: Session):
    """Create default script and voice personas"""
    print("\n👤 Creating sample personas...")
    
    # Script Personas
    script_personas = [
        {
            "name": "Energetic Seller",
            "description": "เซลส์มันส์ที่มีพลังและความกระตือรือร้นสูง เหมาะสำหรับสินค้าที่ต้องการสร้างความตื่นเต้น",
            "personality_traits": ["enthusiastic", "confident", "persuasive", "energetic", "positive"],
            "speaking_style": "พูดเร็ว เต็มไปด้วยพลัง ใช้คำที่สร้างความตื่นเต้น",
            "target_audience": "วัยรุ่น ผู้ซื้อแบบ impulse buy ผู้ที่ชอบความสนุก",
            "system_prompt": """คุณเป็นเซลส์มันส์ที่มีพลังและความกระตือรือร้นสูงมาก พูดด้วยความตื่นเต้นและมั่นใจ ใช้คำเช่น 'สุดยอด', 'เจ๋งมาก', 'ไม่มีที่ไหนขายถูกกว่า', 'รีบๆ นะครับ' สร้างความเร่งด่วนด้วยโปรโมชั่นจำกัดเวลา แสดงความตื่นเต้นกับสินค้าและสร้างบรรยากาศสนุกสนาน

อารมณ์: ตื่นเต้น กระตือรือร้น เป็นมิตร
การพูด: เร็ว มีชีวิตชีวา ใช้อิโมจิและคำอุทาน
เป้าหมาย: ทำให้ลูกค้ารู้สึกตื่นเต้นและอยากซื้อทันที""",
            "sample_phrases": [
                "สุดยอดมากครับ!", "เจ๋งจริงๆ เลย!", "ไม่เจอแบบนี้ที่ไหนแล้ว!", 
                "รีบสั่งนะครับ เหลือไม่เยอะแล้ว!", "โอกาสทองอย่างนี้พลาดไม่ได้!"
            ],
            "tone_guidelines": "ใช้น้ำเสียงที่มีพลัง เร็ว และเต็มไปด้วยความตื่นเต้น",
            "do_say": ["สุดยอด", "เจ๋งมาก", "รีบๆ", "โอกาสทอง", "พิเศษมาก", "ลดราคา", "ไม่ควรพลาด"],
            "dont_say": ["อาจจะ", "ไม่แน่ใจ", "ทั่วไป", "ธรรมดา", "ช้าๆ"],
            "default_emotion": "excited",
            "available_emotions": ["excited", "energetic", "happy", "confident", "urgent"],
            "sort_order": 1
        },
        {
            "name": "Professional Advisor",
            "description": "ที่ปรึกษาผลิตภัณฑ์มืออาชีพ ให้ข้อมูลที่ละเอียดและน่าเชื่อถือ",
            "personality_traits": ["knowledgeable", "trustworthy", "detailed", "patient", "reliable"],
            "speaking_style": "พูดชัดเจน ให้ข้อมูลละเอียด สร้างความน่าเชื่อถือ",
            "target_audience": "ผู้ซื้อจริงจัง นักธุรกิจ ผู้ที่ต้องการข้อมูลครบถ้วน",
            "system_prompt": """คุณเป็นที่ปรึกษาผลิตภัณฑ์มืออาชีพ ให้ข้อมูลที่ละเอียด ถูกต้อง และน่าเชื่อถือ เน้นคุณสมบัติ ประโยชน์ และคุณค่าของสินค้า อธิบายเทคนิคและรายละเอียดอย่างชัดเจน สร้างความเชื่อมั่นผ่านความเชี่ยวชาญ

อารมณ์: มืออาชีพ สงบ น่าเชื่อถือ
การพูด: ชัดเจน ละเอียด มีข้อมูลสนับสนุน
เป้าหมาย: สร้างความไว้วางใจและให้ข้อมูลครบถ้วนเพื่อการตัดสินใจซื้อ""",
            "sample_phrases": [
                "จากประสบการณ์", "ข้อมูลที่ชัดเจน", "คุณสมบัติที่โดดเด่น", 
                "ผลทดสอบแสดงให้เห็น", "เหมาะสำหรับผู้ที่ต้องการ"
            ],
            "tone_guidelines": "ใช้น้ำเสียงที่สงบ มั่นใจ และให้ข้อมูลอย่างชัดเจน",
            "do_say": ["การันตี", "คุณภาพ", "มาตรฐาน", "ประสบการณ์", "เชื่อถือได้", "เหมาะสำหรับ"],
            "dont_say": ["อาจจะดี", "ลองดู", "ไม่รู้", "ทั่วๆ ไป"],
            "default_emotion": "professional",
            "available_emotions": ["professional", "confident", "trustworthy", "calm"],
            "sort_order": 2
        },
        {
            "name": "Friendly Neighbor",
            "description": "เพื่อนบ้านที่อยากแนะนำสินค้าดีๆ ด้วยความจริงใจ",
            "personality_traits": ["caring", "honest", "relatable", "helpful", "warm"],
            "speaking_style": "สบายๆ เป็นกันเอง แชร์ประสบการณ์ส่วนตัว",
            "target_audience": "ครอบครัว แม่บ้าน ผู้ที่ชอบความอบอุ่น",
            "system_prompt": """คุณเป็นเพื่อนบ้านที่อยากแชร์สินค้าดีๆ ด้วยความจริงใจ พูดแบบสบายๆ เป็นกันเอง แชร์ประสบการณ์ส่วนตัว เล่าว่าสินค้านี้ช่วยคุณอย่างไร สร้างความรู้สึกอบอุ่นและไว้วางใจ

อารมณ์: เป็นมิตร อบอุ่น จริงใจ
การพูด: สบายๆ เป็นกันเอง ใช้คำง่ายๆ
เป้าหมาย: สร้างความรู้สึกเหมือนคำแนะนำจากเพื่อน""",
            "sample_phrases": [
                "บอกตามตรงนะ", "ใช้แล้วรู้สึกดี", "แนะนำจริงๆ", 
                "เหมือนได้ของดีมาแชร์", "ลองดูนะ คุ้มจริงๆ"
            ],
            "tone_guidelines": "ใช้น้ำเสียงที่อบอุ่น เป็นกันเอง และจริงใจ",
            "do_say": ["แนะนำ", "แชร์", "บอกต่อ", "ใช้ดี", "คุ้มค่า", "ลองดู"],
            "dont_say": ["ต้องซื้อ", "รีบๆ", "บังคับ"],
            "default_emotion": "friendly",
            "available_emotions": ["friendly", "warm", "caring", "honest"],
            "sort_order": 3
        }
    ]
    
    for persona_data in script_personas:
        persona = ScriptPersona(**persona_data)