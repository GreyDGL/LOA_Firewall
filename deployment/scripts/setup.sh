#!/bin/bash

# LLM Firewall - Quick Setup Script
# This script automates the deployment of the LLM Firewall service

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
FIREWALL_PORT=5001
OLLAMA_PORT=11434
SERVICE_NAME="llm-firewall"

# Logging functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_header() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "🛡️  LLM Firewall Quick Setup"
    echo "=========================================="
    echo -e "${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi

    # Check if ports are available
    if netstat -tulpn 2>/dev/null | grep -q ":${FIREWALL_PORT}"; then
        warn "Port ${FIREWALL_PORT} is already in use. The firewall service might not start properly."
    fi

    if netstat -tulpn 2>/dev/null | grep -q ":${OLLAMA_PORT}"; then
        warn "Port ${OLLAMA_PORT} is already in use. Ollama might not be accessible externally."
    fi

    # Check available disk space (minimum 10GB)
    available_space=$(df . | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        warn "Less than 10GB of disk space available. This might not be sufficient."
    fi

    # Check available memory (minimum 4GB)
    available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt 4096 ]; then
        warn "Less than 4GB of memory available. Performance might be affected."
    fi

    success "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."

    mkdir -p logs config

    # Create initial log file
    touch logs/firewall.log

    # Set proper permissions
    chmod 755 logs config
    chmod 644 logs/firewall.log

    success "Directories created successfully"
}

# Check if required files exist
check_files() {
    log "Checking required files..."

    required_files=("Dockerfile" "docker-compose.yml" "run.py" "pyproject.toml")
    missing_files=()

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done

    if [[ ${#missing_files[@]} -gt 0 ]]; then
        error "Missing required files: ${missing_files[*]}"
    fi

    success "All required files found"
}

# Build Docker image
build_image() {
    log "Building LLM Firewall Docker image..."

    # Use Docker Compose to build
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi

    success "Docker image built successfully"
}

# Deploy the service
deploy_service() {
    log "Deploying LLM Firewall service..."

    # Stop any existing service
    stop_service_quiet

    # Start the service
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    else
        docker compose up -d
    fi

    success "Service deployed successfully"
}

# Stop service (quiet mode for cleanup)
stop_service_quiet() {
    if command -v docker-compose &> /dev/null; then
        docker-compose down 2>/dev/null || true
    else
        docker compose down 2>/dev/null || true
    fi
}

# Wait for service to be ready
wait_for_service() {
    log "Waiting for service to be ready..."

    max_attempts=30
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:${FIREWALL_PORT}/health > /dev/null 2>&1; then
            success "Service is ready!"
            return 0
        fi

        echo -n "."
        sleep 2
        ((attempt++))
    done

    error "Service failed to start within expected time"
}

# Verify deployment
verify_deployment() {
    log "Verifying deployment..."

    # Check if container is running
    if ! docker ps | grep -q "$SERVICE_NAME"; then
        error "Container is not running"
    fi

    # Check health endpoint
    health_response=$(curl -s http://localhost:${FIREWALL_PORT}/health || echo "failed")
    if [[ "$health_response" == "failed" ]]; then
        error "Health check failed"
    fi

    # Parse health response
    if echo "$health_response" | grep -q '"status": "healthy"'; then
        success "Health check passed"
    else
        warn "Health check returned unexpected response"
        echo "$health_response"
    fi

    # Test basic functionality
    test_response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d '{"text": "This is a test message"}' \
        http://localhost:${FIREWALL_PORT}/check || echo "failed")

    if [[ "$test_response" == "failed" ]]; then
        warn "Basic functionality test failed"
    elif echo "$test_response" | grep -q '"is_safe"'; then
        success "Basic functionality test passed"
    else
        warn "Unexpected response from functionality test"
    fi
}

# Show status and next steps
show_status() {
    echo
    success "🎉 LLM Firewall deployment completed successfully!"
    echo
    echo -e "${BLUE}Service Information:${NC}"
    echo "  • LLM Firewall API: http://localhost:${FIREWALL_PORT}"
    echo "  • Ollama API: http://localhost:${OLLAMA_PORT}"
    echo "  • Health Check: http://localhost:${FIREWALL_PORT}/health"
    echo "  • Logs: ./logs/firewall.log"
    echo
    echo -e "${BLUE}Quick Test:${NC}"
    echo "  curl -X POST http://localhost:${FIREWALL_PORT}/check \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"text\": \"Hello, this is a test message\"}'"
    echo
    echo -e "${BLUE}Management Commands:${NC}"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop service: docker-compose down"
    echo "  • Restart service: docker-compose restart"
    echo "  • Update service: docker-compose down && docker-compose up -d --build"
    echo
    echo -e "${BLUE}Documentation:${NC}"
    echo "  • See README.md for detailed API documentation"
    echo "  • Check logs/ directory for service logs"
    echo
}

# Cleanup function for script interruption
cleanup() {
    echo
    warn "Setup interrupted. Cleaning up..."
    stop_service_quiet
    exit 1
}

# Show help
show_help() {
    echo "LLM Firewall Quick Setup Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -p, --port     Set custom port for firewall API (default: 5001)"
    echo "  --no-build     Skip building Docker image (use existing)"
    echo "  --dev          Enable development mode (debug logging)"
    echo
    echo "Examples:"
    echo "  $0                    # Standard deployment"
    echo "  $0 -p 8080           # Deploy on custom port"
    echo "  $0 --dev             # Deploy with debug logging"
    echo
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -p|--port)
                FIREWALL_PORT="$2"
                shift 2
                ;;
            --no-build)
                SKIP_BUILD=true
                shift
                ;;
            --dev)
                DEV_MODE=true
                shift
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

# Update docker-compose for custom port
update_compose_port() {
    if [[ "$FIREWALL_PORT" != "5001" ]]; then
        log "Updating docker-compose.yml for custom port $FIREWALL_PORT"
        sed -i.bak "s/5001:5001/${FIREWALL_PORT}:5001/" docker-compose.yml
    fi
}

# Update environment for dev mode
update_dev_mode() {
    if [[ "${DEV_MODE:-false}" == "true" ]]; then
        log "Enabling development mode"
        export LLM_FIREWALL_DEBUG=true
        export LLM_FIREWALL_LOG_LEVEL=DEBUG
    fi
}

# Main function
main() {
    # Set up signal handlers
    trap cleanup SIGINT SIGTERM

    print_header

    # Parse arguments
    parse_args "$@"

    # Update configuration based on arguments
    update_compose_port
    update_dev_mode

    # Run setup steps
    check_prerequisites
    check_files
    create_directories

    if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
        build_image
    else
        log "Skipping Docker build as requested"
    fi

    deploy_service
    wait_for_service
    verify_deployment
    show_status

    echo -e "${GREEN}Setup completed successfully! 🚀${NC}"
}

# Run main function with all arguments
main "$@"