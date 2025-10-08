#!/bin/bash

# CORTX/Sinergy All Services Startup Script
# This script starts all frontend services on different ports

set -e

echo "🚀 Starting all Sinergy/CORTX services..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if concurrently is installed
if ! command -v concurrently &> /dev/null; then
    echo -e "${YELLOW}⚠️  concurrently not found. Installing...${NC}"
    npm install -g concurrently
fi

echo -e "${BLUE}📋 Service Ports:${NC}"
echo "  • CORTX Designer:  http://localhost:3000"
echo "  • OffermAit:       http://localhost:3001"
echo "  • CORTX Suites:    http://localhost:3002"
echo "  • FedSuite:        http://localhost:3003"
echo ""

# Clean up any processes on required ports
PORTS=(3000 3001 3002 3003)
for PORT in "${PORTS[@]}"; do
    PID=$(lsof -ti :$PORT 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
        echo -e "${YELLOW}⚠️  Port $PORT in use by PID $PID. Killing...${NC}"
        kill -9 $PID 2>/dev/null || true
        sleep 0.5
    fi
done

echo -e "${GREEN}✨ Starting all services...${NC}"
echo ""

# Start all services using concurrently
concurrently \
  --names "DESIGNER,OFFERM,SUITES,FEDSUITE" \
  --prefix-colors "cyan,magenta,green,yellow" \
  --kill-others \
  --kill-others-on-fail \
  "cd /Users/michael/Development/sinergysolutionsllc/cortx-designer/frontend && npm run dev" \
  "cd /Users/michael/Development/OffermAit/frontend && npm run dev -- -p 3001" \
  "cd /Users/michael/Development/cortx-suites/frontend && npm run dev -- -p 3002" \
  "cd /Users/michael/Development/sinergysolutionsllc/fedsuite/frontend && npm run dev -- -p 3003"
