#!/bin/bash

# Unified CORTX Platform Startup Script
# Starts both backend services (Docker) and frontend apps (Next.js)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 CORTX Platform - Complete Startup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Docker is running
log_info "Checking Docker status..."
if ! docker info > /dev/null 2>&1; then
  log_error "Docker is not running!"
  echo ""
  echo "Please start Docker Desktop and try again."
  echo ""
  echo "Options:"
  echo "  1. Start Docker Desktop manually"
  echo "  2. Run: open -a Docker"
  echo ""
  exit 1
fi
log_success "Docker is running"
echo ""

# Start backend services
log_info "🐳 Starting backend services with Docker Compose..."
cd "${SCRIPT_DIR}"

if [ -f "${SCRIPT_DIR}/start-cortx.sh" ]; then
  ./start-cortx.sh
else
  log_error "start-cortx.sh not found"
  exit 1
fi

echo ""
log_info "⏳ Waiting for backend services to be healthy (30 seconds)..."
sleep 30

# Check backend health
log_info "Checking backend service health..."
GATEWAY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/healthz 2>/dev/null || echo "000")

if [ "$GATEWAY_STATUS" = "200" ]; then
  log_success "Gateway is healthy"
else
  log_error "Gateway is not responding (status: $GATEWAY_STATUS)"
  log_info "Check logs with: docker compose logs gateway"
fi

echo ""

# Start frontend applications
log_info "🎨 Starting frontend applications..."
if [ -f "${SCRIPT_DIR}/start-all.sh" ]; then
  # Run in background and capture PID
  nohup "${SCRIPT_DIR}/start-all.sh" > /tmp/cortx-frontends.log 2>&1 &
  FRONTEND_PID=$!
  echo $FRONTEND_PID > /tmp/cortx-frontends.pid

  log_success "Frontend applications starting (PID: $FRONTEND_PID)"
  log_info "Frontend logs: tail -f /tmp/cortx-frontends.log"
else
  log_error "start-all.sh not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CORTX Platform Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend Applications:"
echo "   • CORTX Designer:  http://localhost:3000"
echo "   • OffermAit:       http://localhost:3001"
echo "   • CORTX Suites:    http://localhost:3002"
echo "   • FedSuite:        http://localhost:3003"
echo ""
echo "⚙️  Backend Services:"
echo "   • Gateway:         http://localhost:8080"
echo "   • Identity:        http://localhost:8082"
echo "   • Validation:      http://localhost:8083"
echo "   • AI Broker:       http://localhost:8085"
echo "   • Workflow:        http://localhost:8130"
echo "   • Compliance:      http://localhost:8135"
echo "   • Ledger:          http://localhost:8136"
echo "   • OCR:             http://localhost:8137"
echo "   • RAG:             http://localhost:8138"
echo ""
echo "📋 Management Commands:"
echo "   • Backend logs:    docker compose logs -f [service]"
echo "   • Frontend logs:   tail -f /tmp/cortx-frontends.log"
echo "   • Stop backend:    docker compose down"
echo "   • Stop frontend:   kill \$(cat /tmp/cortx-frontends.pid)"
echo "   • Stop all:        ./stop-everything.sh"
echo ""
