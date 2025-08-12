#!/bin/bash

echo "🚀 Setting up AI Live Commerce Platform..."

# Create all directories
echo "Creating directories..."
mkdir -p app/{core,models,api/v1,services,integrations,utils}
mkdir -p frontend/{static/{css,js,assets},templates}
mkdir -p logs data uploads

# Create all __init__.py files
echo "Creating __init__.py files..."
find app -type d -exec touch {}/__init__.py \;

# Create basic .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVFILE'
# Application
APP_NAME="AI Live Commerce Platform"
APP_VERSION="1.0.0"
DEBUG=True

# Database
DATABASE_URL=sqlite:///./ai_live_commerce.db

# Security
SECRET_KEY=your-secret-key-change-this-immediately
ENCRYPTION_KEY=your-encryption-key-change-this

# Logging
LOG_LEVEL=INFO
ENVFILE
fi

echo "✅ Setup complete!"
echo ""
echo "Now run:"
echo "  python main_minimal.py initdb"
