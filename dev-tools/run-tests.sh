#!/bin/bash
# Testing Helper Script

echo "🧪 Running AI Live Commerce Tests"

source venv/bin/activate

# Manual testing checklist
echo "📋 Manual Testing Checklist:"
echo "1. TTS Service Test:"
echo "   curl -X POST http://localhost:8000/api/v1/avatar/speak \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"text\": \"Hello, this is a test\", \"language\": \"en\"}'"
echo ""
echo "2. Script Generation Test:"
echo "   curl -X POST http://localhost:8000/api/v1/scripts/generate \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"product_name\": \"Test Product\", \"features\": [\"feature1\"], \"language\": \"th\"}'"
echo ""
echo "3. Frontend Test:"
echo "   Open: http://localhost:8000"
echo "   Open: http://localhost:8000/avatar.html"

