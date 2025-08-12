import os
import base64
import secrets
from passlib.context import CryptContext
from dotenv import load_dotenv
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # Try current directory
    load_dotenv()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    print("=" * 50)
    print("⚠️  ERROR: ENCRYPTION_KEY not found!")
    print("Please add to .env file:")
    print("ENCRYPTION_KEY=SgJOc-ZTdTacmYi9fBBG2d-oNzXYD1S497zyVfQHocU=")
    print("=" * 50)
    # Use default for emergency
    ENCRYPTION_KEY = "SgJOc-ZTdTacmYi9fBBG2d-oNzXYD1S497zyVfQHocU="

class SecurityManager:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except:
            return False
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
