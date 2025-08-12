#!/bin/bash

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}=================================================${NC}"
echo -e "${GREEN}🚀 AI Live Commerce Platform${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo "Starting server with auto-reload..."
echo ""
echo -e "${GREEN}📱 Dashboard:${NC} http://localhost:8000"
echo -e "${GREEN}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${GREEN}📊 Products:${NC} http://localhost:8000/api/products"
echo ""
echo -e "${BLUE}=================================================${NC}"
echo "Press CTRL+C to stop"
echo ""

# Run with uvicorn (recommended)
uvicorn run_server:app --reload --host 0.0.0.0 --port 8000
