#!/bin/bash

# LLM Firewall Model Setup Script
# This script downloads and configures the required AI models for the firewall
# Model names are abstracted for security purposes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLLAMA_HOST="localhost:11434"
OLLAMA_API_URL="http://${OLLAMA_HOST}/api"
MODELS_DIR="/tmp/firewall_models"
LOG_FILE="/tmp/model_setup.log"

# Model configurations (abstracted names)
declare -A MODELS=(
    ["guard_primary"]="llama-guard3"
    ["guard_secondary"]="granite3-guardian:8b"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Function to check if Ollama is running
check_ollama_status() {
    print_status "Checking Ollama service status..."
    
    if ! pgrep -x "ollama" > /dev/null; then
        print_warning "Ollama service not running. Starting Ollama..."
        ollama serve > /dev/null 2>&1 &
        sleep 5
        
        if ! pgrep -x "ollama" > /dev/null; then
            print_error "Failed to start Ollama service"
            return 1
        fi
    fi
    
    # Wait for API to be ready
    local retries=0
    local max_retries=30
    
    while [ $retries -lt $max_retries ]; do
        if curl -s "${OLLAMA_API_URL}/tags" > /dev/null 2>&1; then
            print_success "Ollama API is ready"
            return 0
        fi
        
        print_status "Waiting for Ollama API... (attempt $((retries + 1))/$max_retries)"
        sleep 2
        retries=$((retries + 1))
    done
    
    print_error "Ollama API not responding after $max_retries attempts"
    return 1
}

# Function to check if a model is already available
check_model_exists() {
    local model_name="$1"
    
    if curl -s "${OLLAMA_API_URL}/tags" | grep -q "\"name\":\"${model_name}\""; then
        return 0
    else
        return 1
    fi
}

# Function to download a model with progress tracking
download_model() {
    local model_alias="$1"
    local model_name="$2"
    
    print_status "Downloading AI security model: ${model_alias}..."
    
    # Check if model already exists
    if check_model_exists "$model_name"; then
        print_success "Model ${model_alias} already available"
        return 0
    fi
    
    # Create a temporary script to hide the actual model name from process list
    local temp_script="/tmp/pull_${model_alias}.sh"
    cat > "$temp_script" << EOF
#!/bin/bash
ollama pull "$model_name" 2>&1 | while IFS= read -r line; do
    if [[ "\$line" == *"pulling"* ]] || [[ "\$line" == *"downloading"* ]]; then
        echo "[INFO] Downloading ${model_alias} components..."
    elif [[ "\$line" == *"verifying"* ]]; then
        echo "[INFO] Verifying ${model_alias} integrity..."
    elif [[ "\$line" == *"success"* ]] || [[ "\$line" == *"already exists"* ]]; then
        echo "[SUCCESS] ${model_alias} ready"
    else
        echo "\$line"
    fi
done
EOF
    
    chmod +x "$temp_script"
    
    # Execute the download with abstracted output
    if "$temp_script"; then
        print_success "Model ${model_alias} downloaded successfully"
        rm -f "$temp_script"
        return 0
    else
        print_error "Failed to download model ${model_alias}"
        rm -f "$temp_script"
        return 1
    fi
}

# Function to validate model functionality
validate_model() {
    local model_alias="$1"
    local model_name="$2"
    
    print_status "Validating ${model_alias} functionality..."
    
    # Create a simple test request
    local test_payload='{"model":"'$model_name'","messages":[{"role":"user","content":"test"}],"stream":false}'
    
    if curl -s -X POST "${OLLAMA_API_URL}/chat" \
        -H "Content-Type: application/json" \
        -d "$test_payload" | grep -q "message"; then
        print_success "Model ${model_alias} validation successful"
        return 0
    else
        print_warning "Model ${model_alias} validation failed (may still work)"
        return 1
    fi
}

# Function to update docker-compose configuration
update_docker_compose() {
    local compose_file="$1"
    
    # Detect the correct image name from existing compose file or available images
    local image_name=""
    
    # First, try to find existing image name in compose file
    if [ -f "$compose_file" ]; then
        image_name=$(grep -E "^\s*image:" "$compose_file" | head -1 | sed 's/.*image: *//' | tr -d '"' | tr -d "'")
    fi
    
    # If no image found in compose file, try to detect from loaded images
    if [ -z "$image_name" ] || [[ "$image_name" == *"\$"* ]]; then
        # Look for firewall images in docker
        image_name=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -E "firewall|llm.*firewall" | head -1)
        
        # If still no image found, use a default that will require manual specification
        if [ -z "$image_name" ]; then
            image_name="llm-firewall:latest"
            print_warning "Could not detect image name. Using default: $image_name"
            print_status "Make sure to load your image first: docker load < your-image.tar"
        fi
    fi
    
    print_status "Updating docker-compose configuration with image: $image_name"
    
    # Create backup if file exists
    if [ -f "$compose_file" ]; then
        cp "$compose_file" "${compose_file}.backup"
    fi
    
    # Update the compose file to use host networking and proper Ollama configuration
    cat > "$compose_file" << EOF
services:
  llm-firewall:
    image: $image_name
    container_name: llm-firewall-client
    restart: unless-stopped
    
    # Use host networking for direct access to host Ollama
    network_mode: host
    
    # Environment configuration
    environment:
      - LLM_FIREWALL_HOST=0.0.0.0
      - LLM_FIREWALL_PORT=5001
      - LLM_FIREWALL_LOG_LEVEL=INFO
      - LLM_FIREWALL_DEBUG=false
      - OLLAMA_HOST=localhost:11434
      - PYTHONUNBUFFERED=1
    
    # Volume mounts
    volumes:
      - ./logs:/app/logs
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
    
    # Start command
    command: ["python3", "run.pyc"]

# Network configuration ensures:
# - Firewall API accessible on host port 5001
# - Ollama remains on localhost:11434 (not externally accessible)
# - Models stay hidden from external access
EOF
    
    print_success "Docker compose configuration updated with image: $image_name"
}

# Function to setup system requirements
setup_system() {
    print_status "Checking system requirements..."
    
    # Check if running as root or with sudo access
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. Consider using a non-root user with sudo access."
    fi
    
    # Check available disk space (need at least 10GB for models)
    local available_space=$(df /tmp | awk 'NR==2{print $4}')
    local required_space=10485760  # 10GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        print_error "Insufficient disk space. Need at least 10GB free."
        return 1
    fi
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_error "curl is required but not installed"
        return 1
    fi
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama is not installed. Please install Ollama first."
        print_status "Install command: curl -fsSL https://ollama.ai/install.sh | sh"
        return 1
    fi
    
    print_success "System requirements check passed"
}

# Function to create logs directory
setup_logs() {
    print_status "Setting up logs directory..."
    
    mkdir -p logs
    chmod 755 logs
    
    print_success "Logs directory configured"
}

# Main function
main() {
    echo "============================================"
    echo "    LLM Firewall Model Setup"
    echo "============================================"
    echo ""
    
    # Initialize log file
    echo "Model setup started at $(date)" > "$LOG_FILE"
    
    # Setup system
    if ! setup_system; then
        exit 1
    fi
    
    # Setup logs directory
    setup_logs
    
    # Check Ollama status
    if ! check_ollama_status; then
        exit 1
    fi
    
    # Download and validate models
    local failed_models=0
    for model_alias in "${!MODELS[@]}"; do
        model_name="${MODELS[$model_alias]}"
        
        if download_model "$model_alias" "$model_name"; then
            validate_model "$model_alias" "$model_name" || true
        else
            failed_models=$((failed_models + 1))
        fi
        
        echo ""
    done
    
    # Check if any models failed to download
    if [ $failed_models -gt 0 ]; then
        print_error "$failed_models model(s) failed to download"
        print_status "You may need to retry or check your internet connection"
        exit 1
    fi
    
    # Update docker-compose if file exists
    for compose_file in docker-compose.yml docker-compose.*.yml; do
        if [ -f "$compose_file" ]; then
            update_docker_compose "$compose_file"
            break
        fi
    done
    
    echo ""
    echo "============================================"
    print_success "Model setup completed successfully!"
    echo "============================================"
    echo ""
    print_status "Next steps:"
    echo "  1. Load your Docker image: docker load < your-firewall-image.tar"
    echo "  2. Start the firewall: docker compose up -d"
    echo "  3. Test the deployment: curl http://localhost:5001/health"
    echo ""
    print_status "Logs saved to: $LOG_FILE"
    
    # Cleanup temporary files
    rm -rf "$MODELS_DIR"
}

# Handle script termination
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -f /tmp/pull_*.sh
    rm -rf "$MODELS_DIR"
}

trap cleanup EXIT

# Run main function
main "$@"