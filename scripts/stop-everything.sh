#!/bin/bash

# Unified CORTX Platform Stop Script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 CORTX Platform - Shutdown"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Stop frontend applications
if [ -f /tmp/cortx-frontends.pid ]; then
  FRONTEND_PID=$(cat /tmp/cortx-frontends.pid)
  log_info "Stopping frontend applications (PID: $FRONTEND_PID)..."

  # Kill the main process
  kill $FRONTEND_PID 2>/dev/null || true

  # Kill all child processes (concurrently spawned Next.js servers)
  pkill -P $FRONTEND_PID 2>/dev/null || true

  # Also kill any remaining Next.js dev servers on our ports
  for port in 3000 3001 3002 3003; do
    PID=$(lsof -ti tcp:$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
      kill -9 $PID 2>/dev/null || true
    fi
  done

  rm /tmp/cortx-frontends.pid
  log_success "Frontend applications stopped"
else
  log_info "No frontend PID file found, checking ports..."
  for port in 3000 3001 3002 3003; do
    PID=$(lsof -ti tcp:$port 2>/dev/null || true)
    if [ ! -z "$PID" ]; then
      log_info "Killing process on port $port (PID: $PID)"
      kill -9 $PID 2>/dev/null || true
    fi
  done
fi

echo ""

# Stop backend services
log_info "Stopping backend services..."
cd "${SCRIPT_DIR}"

if docker compose version &> /dev/null; then
  docker compose down
else
  docker-compose down
fi

log_success "Backend services stopped"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CORTX Platform Stopped"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
