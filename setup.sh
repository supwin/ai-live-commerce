#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AI Live Commerce Platform - Setup Script${NC}"
echo "================================================"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
echo "Python version: $python_version"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install --upgrade pip
pip install pydantic-settings email-validator
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p app/{core,models,api/v1,services,integrations,utils}
mkdir -p frontend/{static/{css,js,assets},templates}
mkdir -p logs data uploads
mkdir -p tests/{unit,integration,e2e}

# Create __init__.py files
echo -e "${YELLOW}Creating __init__.py files...${NC}"
touch app/__init__.py
touch app/core/__init__.py
touch app/models/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/services/__init__.py
touch app/integrations/__init__.py
touch app/utils/__init__.py

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env 2>/dev/null || cat > .env << 'EOF'
# Application
APP_NAME="AI Live Commerce Platform"
APP_VERSION="1.0.0"
DEBUG=True

# Server
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Database
DATABASE_URL=sqlite:///./ai_live_commerce.db

# Security (Generate new keys!)
SECRET_KEY=change-this-to-a-random-secret-key-min-32-chars
ENCRYPTION_KEY=change-this-to-base64-encoded-32-bytes-key

# AI Services (Add your keys)
OPENAI_API_KEY=
ELEVENLABS_API_KEY=

# OBS Settings
OBS_WEBSOCKET_HOST=localhost
OBS_WEBSOCKET_PORT=4455
OBS_WEBSOCKET_PASSWORD=

# Logging
LOG_LEVEL=INFO
EOF
    
    # Generate security keys
    echo -e "${YELLOW}Generating security keys...${NC}"
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    ENCRYPTION_KEY=$(python3 -c "import base64, secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())")
    
    # Update .env with generated keys (for Linux/Mac)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i '' "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    else
        # Linux
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        sed -i "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
    fi
    
    echo -e "${GREEN}✅ Generated new security keys${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python main.py initdb

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run: python main.py createsuperuser"
echo "3. Run: python main.py"
echo ""
echo "Dashboard will be available at: http://localhost:8000"