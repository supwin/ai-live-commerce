#!/bin/bash

echo "🎭 Setting up Live2D Avatar System"
echo "==================================="

# Install required packages
echo "📦 Installing Python packages..."
pip install numpy websockets aiofiles

# Create directories
echo "📁 Creating directories..."
mkdir -p app/services
mkdir -p app/api/v1
mkdir -p frontend/models
mkdir -p frontend/assets/avatar

# Download sample Live2D model (optional)
echo "📥 Downloading sample avatar..."
# We'll use CSS avatar for now, Live2D models need licensing

echo "✅ Avatar system setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Copy avatar_service.py to app/services/"
echo "2. Copy avatar.py to app/api/v1/"
echo "3. Copy avatar.html to frontend/"
echo "4. Restart server"
echo ""
echo "📱 Access avatar at: http://localhost:8000/avatar"
