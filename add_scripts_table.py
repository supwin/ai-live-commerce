#!/usr/bin/env python3
"""
Add ProductScript table to existing database
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from app.core.database import engine
import os

def add_scripts_table():
    """Add product_scripts table to database"""
    
    print("🔧 Adding ProductScript table...")
    
    # SQL to create product_scripts table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS product_scripts (
        id TEXT PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        product_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        script_type TEXT NOT NULL,
        usage_count INTEGER DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY(product_id) REFERENCES products(id)
    );
    """
    
    try:
        # Check if table exists
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if 'product_scripts' in existing_tables:
            print("✅ ProductScript table already exists!")
            return True
        
        # Create table using raw SQL
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            
        print("✅ ProductScript table created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def verify_table():
    """Verify the table was created"""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'product_scripts' in tables:
            columns = inspector.get_columns('product_scripts')
            print("\n📊 Table structure:")
            for col in columns:
                print(f"   - {col['name']}: {col['type']}")
            return True
        else:
            print("❌ Table not found")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying table: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration - Add Scripts Table")
    print("=" * 50)
    
    if add_scripts_table():
        if verify_table():
            print("\n🎉 Migration completed successfully!")
            print("\n📝 Next steps:")
            print("1. Uncomment the relationship in app/models/product.py")
            print("2. Restart the server")
        else:
            print("\n💥 Table creation succeeded but verification failed!")
    else:
        print("\n💥 Migration failed!")