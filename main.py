# main_minimal.py - Minimal version for database initialization
import sys
import os
from pathlib import Path

# Ensure app module can be imported
sys.path.insert(0, str(Path(__file__).parent))

def init_db():
    """Initialize database with sample data"""
    # Import here to avoid circular imports
    from app.core.database import engine, Base, SessionLocal
    from app.models.user import User
    from app.models.product import Product
    from app.models.chat import ChatMessage, ChatSession
    from app.core.security import SecurityManager
    
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create sample user
        user = db.query(User).filter(User.username == "demo").first()
        if not user:
            user = User(
                email="demo@example.com",
                username="demo",
                hashed_password=SecurityManager.get_password_hash("demo123"),
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("✅ Created demo user (username: demo, password: demo123)")
        else:
            print("ℹ️ Demo user already exists")
        
        # Create sample products
        products_data = [
            {
                "name": "AI Smart Camera",
                "price": 2999.0,
                "description": "กล้อง AI อัจฉริยะ ตรวจจับการเคลื่อนไหว",
                "features": ["1080p HD", "Night Vision", "Two-way Audio"],
                "stock": 50,
                "category": "Electronics",
                "sku": "CAM001"
            },
            {
                "name": "Wireless Earbuds Pro",
                "price": 1599.0,
                "description": "หูฟังไร้สาย เสียงคุณภาพสูง",
                "features": ["Noise Cancelling", "30hr Battery", "Waterproof"],
                "stock": 100,
                "category": "Audio",
                "sku": "EAR001"
            }
        ]
        
        for product_data in products_data:
            # Check if product already exists
            existing = db.query(Product).filter(Product.sku == product_data["sku"]).first()
            if not existing:
                product = Product(**product_data, user_id=user.id)
                db.add(product)
                print(f"✅ Added product: {product_data['name']}")
            else:
                print(f"ℹ️ Product already exists: {product_data['name']}")
        
        db.commit()
        print("\n✅ Database initialized successfully!")
        
        # Show summary
        user_count = db.query(User).count()
        product_count = db.query(Product).count()
        print(f"\n📊 Database Summary:")
        print(f"   - Users: {user_count}")
        print(f"   - Products: {product_count}")
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

def create_superuser():
    """Create a superuser account"""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.core.security import SecurityManager
    import getpass
    
    db = SessionLocal()
    
    try:
        print("\n🔐 Create Superuser Account")
        print("-" * 30)
        
        email = input("Email: ")
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        password_confirm = getpass.getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match!")
            return
        
        # Check if user exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing:
            print("❌ User with this email or username already exists!")
            return
        
        user = User(
            email=email,
            username=username,
            hashed_password=SecurityManager.get_password_hash(password),
            is_superuser=True,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        
        print(f"\n✅ Superuser '{username}' created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating superuser: {e}")
        db.rollback()
    finally:
        db.close()

def test_connection():
    """Test database connection"""
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("\n🚀 AI Live Commerce Platform - Database Tool")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "initdb":
            if test_connection():
                init_db()
        elif command == "createsuperuser":
            if test_connection():
                create_superuser()
        elif command == "test":
            test_connection()
        else:
            print(f"Unknown command: {command}")
            print("\nAvailable commands:")
            print("  python main_minimal.py initdb         - Initialize database")
            print("  python main_minimal.py createsuperuser - Create admin user")
            print("  python main_minimal.py test           - Test connection")
    else:
        print("\nUsage: python main_minimal.py [command]")
        print("\nCommands:")
        print("  initdb         - Initialize database with sample data")
        print("  createsuperuser - Create superuser account")
        print("  test           - Test database connection")