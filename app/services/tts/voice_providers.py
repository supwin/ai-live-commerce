# app/services/tts/voice_providers.py
"""Voice Providers Configuration and Management"""

from typing import Dict, Any

class VoiceProviders:
    """Voice Providers Configuration Manager"""
    
    @staticmethod
    def get_edge_voices() -> Dict[str, Any]:
        """รายการ Edge TTS voices ที่รองรับอารมณ์"""
        return {
            "th_female_professional": {
                "voice": "th-TH-PremwadeeNeural",
                "name": "Premwadee (Thai Female Professional)",
                "language": "th-TH",
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
            },
            "th_male_casual": {
                "voice": "th-TH-NiwatNeural", 
                "name": "Niwat (Thai Male Casual)",
                "language": "th-TH",
                "gender": "male",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious"]
            },
            "th_female_warm": {
                "voice": "th-TH-AcharaNeural",
                "name": "Achara (Thai Female Warm)",
                "language": "th-TH", 
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle"]
            },
            "en_female_professional": {
                "voice": "en-US-JennyNeural",
                "name": "Jenny (English Female Professional)",
                "language": "en-US",
                "gender": "female",
                "emotions": ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
            }
        }
    
    @staticmethod
    def get_elevenlabs_voices() -> Dict[str, Any]:
        """รายการ ElevenLabs voices"""
        try:
            return {
                "adam": {
                    "voice_id": "pNInz6obpgDQGcFmaJgB",
                    "name": "Adam (English Male)",
                    "language": "en",
                    "gender": "male",
                    "emotions": ["neutral", "excited", "sad", "angry", "cheerful", "serious"]
                },
                "bella": {
                    "voice_id": "EXAVITQu4vr4xnSDxMaL",
                    "name": "Bella (English Female)",
                    "language": "en", 
                    "gender": "female",
                    "emotions": ["neutral", "excited", "sad", "angry", "cheerful", "serious", "gentle"]
                },
                "rachel": {
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "name": "Rachel (English Female Professional)",
                    "language": "en",
                    "gender": "female", 
                    "emotions": ["neutral", "professional", "confident", "cheerful", "serious"]
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error getting ElevenLabs voices: {e}")
            return {}
    
    @staticmethod
    def get_azure_voices() -> Dict[str, Any]:
        """รายการ Azure Speech voices"""
        try:
            return {
                "th_female_premium": {
                    "voice": "th-TH-PremwadeeNeural",
                    "name": "Premwadee Premium (Azure)",
                    "language": "th-TH",
                    "gender": "female", 
                    "emotions": ["cheerful", "sad", "angry", "fearful", "serious", "gentle"]
                },
                "th_male_premium": {
                    "voice": "th-TH-NiwatNeural",
                    "name": "Niwat Premium (Azure)",
                    "language": "th-TH",
                    "gender": "male",
                    "emotions": ["cheerful", "sad", "angry", "fearful", "serious"]
                }
            }
            
        except Exception as e:
            print(f"⚠️ Error getting Azure voices: {e}")
            return {}

    @staticmethod
    def get_emotions_for_provider(provider: str) -> list:
        """รายการอารมณ์ที่ provider รองรับ"""
        if provider == "edge":
            return ["cheerful", "sad", "angry", "fearful", "disgruntled", "serious", "affectionate", "gentle", "envious"]
        elif provider == "elevenlabs":
            return ["neutral", "excited", "sad", "angry", "cheerful", "serious", "gentle"]
        elif provider == "azure":
            return ["cheerful", "sad", "angry", "fearful", "serious", "gentle"]
        else:
            return ["neutral"]
    
    @staticmethod
    def get_emotion_mapping() -> Dict[str, str]:
        """แปลงอารมณ์ให้เหมาะสมกับ SSML"""
        return {
            "excited": "cheerful",
            "happy": "cheerful", 
            "professional": "neutral",
            "friendly": "gentle",
            "confident": "neutral",
            "energetic": "cheerful",
            "calm": "gentle",
            "urgent": "neutral"
        }
    
    @staticmethod
    def get_prosody_settings(emotion: str) -> Dict[str, str]:
        """กำหนดการตั้งค่า prosody ตามอารมณ์"""
        settings = {
            "excited": {"rate": "+20%", "pitch": "+15%"},
            "energetic": {"rate": "+15%", "pitch": "+12%"},
            "urgent": {"rate": "+25%", "pitch": "medium"},
            "calm": {"rate": "-10%", "pitch": "-5%"},
            "professional": {"rate": "+5%", "pitch": "medium"},
            "friendly": {"rate": "+10%", "pitch": "+10%"},
            "happy": {"rate": "medium", "pitch": "+10%"},
            "sad": {"rate": "medium", "pitch": "-15%"},
            "confident": {"rate": "medium", "pitch": "+8%"}
        }
        return settings.get(emotion, {"rate": "medium", "pitch": "medium"})
    
    @staticmethod
    def get_emotional_prefixes() -> Dict[str, str]:
        """เพิ่ม emotional context ให้กับข้อความสำหรับ AI voices"""
        return {
            "excited": "ด้วยความตื่นเต้นและกระตือรือร้น: ",
            "happy": "ด้วยความสุขและความยินดี: ",
            "professional": "ด้วยมาตรการทางวิชาชีพ: ",
            "friendly": "ด้วยความเป็นมิตรและอบอุ่น: ",
            "confident": "ด้วยความมั่นใจและแน่วแน่: ",
            "energetic": "ด้วยพลังและความกระปรี้กระเปร่า: ",
            "calm": "ด้วยความสงบและใจเย็น: ",
            "urgent": "ด้วยความเร่งด่วนและจำกัดเวลา: "
        }