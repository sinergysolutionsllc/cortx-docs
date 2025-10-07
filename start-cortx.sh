#!/bin/bash
set -e

# CORTX Multi-Repo Orchestration Script
# Clones/updates all service repos and starts the platform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS_DIR="${SCRIPT_DIR}/repos"
ORG="sinergysolutionsllc"

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Services to clone/update
SERVICES=(
  "gateway"
  "identity"
  "validation"
  "ai-broker"
  "workflow"
  "compliance"
  "ledger"
  "ocr"
  "rag"
)

# Also clone shared repos
SHARED_REPOS=(
  "cortx-platform"
  "cortx-sdks"
)

log_info() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

# Create repos directory
mkdir -p "${REPOS_DIR}"

# Function to clone or update a repo
sync_repo() {
  local repo_name=$1
  local repo_path="${REPOS_DIR}/${repo_name}"

  if [ -d "${repo_path}/.git" ]; then
    log_info "Updating ${repo_name}..."
    cd "${repo_path}"

    # Stash any local changes
    if ! git diff-index --quiet HEAD --; then
      log_warning "Local changes detected in ${repo_name}, stashing..."
      git stash
    fi

    # Pull latest
    if git pull origin main 2>/dev/null || git pull origin master 2>/dev/null; then
      log_success "Updated ${repo_name}"
    else
      log_warning "Could not update ${repo_name} (may be on different branch)"
    fi

    cd "${SCRIPT_DIR}"
  else
    log_info "Cloning ${repo_name}..."
    if gh repo clone "${ORG}/${repo_name}" "${repo_path}"; then
      log_success "Cloned ${repo_name}"
    else
      log_error "Failed to clone ${repo_name}"
      return 1
    fi
  fi
}

# Main execution
main() {
  log_info "🚀 Starting CORTX Platform Setup"
  echo ""

  # Check prerequisites
  log_info "Checking prerequisites..."

  if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed. Install with: brew install gh"
    exit 1
  fi

  if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed"
    exit 1
  fi

  if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose is not installed"
    exit 1
  fi

  log_success "Prerequisites check passed"
  echo ""

  # Sync shared repos
  log_info "📦 Syncing shared repositories..."
  for repo in "${SHARED_REPOS[@]}"; do
    sync_repo "${repo}"
  done
  echo ""

  # Sync service repos
  log_info "🔧 Syncing service repositories..."
  for service in "${SERVICES[@]}"; do
    sync_repo "${service}"
  done
  echo ""

  # Check for .env file
  if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    log_warning ".env file not found, creating from .env.example..."
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
      cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
      log_info "Edit .env file to configure your environment"
    else
      log_warning "No .env.example found, using defaults"
    fi
  fi
  echo ""

  # Start services
  log_info "🐳 Starting CORTX Platform with Docker Compose..."

  # Use docker compose (new) or docker-compose (old)
  if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
  else
    COMPOSE_CMD="docker-compose"
  fi

  # Build and start services
  log_info "Building and starting services (this may take a few minutes)..."
  if ${COMPOSE_CMD} up -d --build; then
    log_success "CORTX Platform started successfully!"
    echo ""

    log_info "📊 Service Status:"
    ${COMPOSE_CMD} ps
    echo ""

    log_info "📝 Access points:"
    echo "  Gateway:     http://localhost:8080"
    echo "  Identity:    http://localhost:8082"
    echo "  Validation:  http://localhost:8083"
    echo "  AI Broker:   http://localhost:8085"
    echo "  Workflow:    http://localhost:8130"
    echo "  Compliance:  http://localhost:8135"
    echo "  Ledger:      http://localhost:8136"
    echo "  OCR:         http://localhost:8137"
    echo "  RAG:         http://localhost:8138"
    echo ""

    log_info "📋 Useful commands:"
    echo "  View logs:        ${COMPOSE_CMD} logs -f [service]"
    echo "  Stop all:         ${COMPOSE_CMD} down"
    echo "  Restart service:  ${COMPOSE_CMD} restart [service]"
    echo "  View status:      ${COMPOSE_CMD} ps"
    echo ""

  else
    log_error "Failed to start services"
    exit 1
  fi
}

# Run main
main "$@"
