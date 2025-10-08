#!/bin/bash

# CORTX Platform Status Checker

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_service() {
  local name=$1
  local url=$2
  local response=$(curl -s -o /dev/null -w "%{http_code}" -m 2 "$url" 2>/dev/null || echo "000")

  if [ "$response" = "200" ]; then
    echo -e "  ${GREEN}✓${NC} $name - $url"
    return 0
  else
    echo -e "  ${RED}✗${NC} $name - $url ${YELLOW}(HTTP $response)${NC}"
    return 1
  fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 CORTX Platform Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Docker
echo -e "${BLUE}🐳 Docker:${NC}"
if docker info > /dev/null 2>&1; then
  echo -e "  ${GREEN}✓${NC} Docker daemon is running"
else
  echo -e "  ${RED}✗${NC} Docker daemon is NOT running"
fi
echo ""

# Check Infrastructure
echo -e "${BLUE}🗄️  Infrastructure:${NC}"
if docker ps --filter "name=cortx-postgres" --filter "status=running" | grep -q cortx-postgres; then
  echo -e "  ${GREEN}✓${NC} PostgreSQL (cortx-postgres)"
else
  echo -e "  ${RED}✗${NC} PostgreSQL (cortx-postgres)"
fi

if docker ps --filter "name=cortx-redis" --filter "status=running" | grep -q cortx-redis; then
  echo -e "  ${GREEN}✓${NC} Redis (cortx-redis)"
else
  echo -e "  ${RED}✗${NC} Redis (cortx-redis)"
fi
echo ""

# Check Backend Services
echo -e "${BLUE}⚙️  Backend Services:${NC}"
check_service "Gateway    " "http://localhost:8080/healthz"
check_service "Identity   " "http://localhost:8082/healthz"
check_service "Validation " "http://localhost:8083/healthz"
check_service "AI Broker  " "http://localhost:8085/healthz"
check_service "Workflow   " "http://localhost:8130/healthz"
check_service "Compliance " "http://localhost:8135/healthz"
check_service "Ledger     " "http://localhost:8136/healthz"
check_service "OCR        " "http://localhost:8137/healthz"
check_service "RAG        " "http://localhost:8138/healthz"
echo ""

# Check Frontend Applications
echo -e "${BLUE}📱 Frontend Applications:${NC}"
check_service "Designer   " "http://localhost:3000"
check_service "OffermAit  " "http://localhost:3001"
check_service "Suites     " "http://localhost:3002"
check_service "FedSuite   " "http://localhost:3003"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
