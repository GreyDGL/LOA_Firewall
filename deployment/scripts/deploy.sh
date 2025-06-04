#!/bin/bash

# LLM Firewall Production Deployment Script
# This script helps automate the deployment process for different scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
CUSTOMER_ID=""
SECRET_KEY=""
DURATION_DAYS=180
IMAGE_TAG=""
REGISTRY=""
FEATURES="basic"
ACTION=""

# Print usage
usage() {
    echo "LLM Firewall Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  build-client    Build client-specific image with embedded license"
    echo "  deploy-local    Deploy locally for development/testing"
    echo "  validate        Validate existing license"
    echo "  renew          Renew license for existing client"
    echo ""
    echo "Options:"
    echo "  --customer ID           Customer identifier (required for build-client)"
    echo "  --secret KEY           Master secret key (required)"
    echo "  --days DAYS            License duration in days (default: 180)"
    echo "  --tag TAG              Docker image tag (default: llm-firewall:CUSTOMER)"
    echo "  --registry URL         Docker registry URL for push"
    echo "  --features LIST        Comma-separated feature list (default: basic)"
    echo ""
    echo "Examples:"
    echo "  $0 build-client --customer \"Acme Corp\" --secret \"mysecret123\" --days 365"
    echo "  $0 deploy-local --secret \"mysecret123\""
    echo "  $0 validate --secret \"mysecret123\""
    echo ""
}

# Parse command line arguments
parse_args() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi

    ACTION=$1
    shift

    while [[ $# -gt 0 ]]; do
        case $1 in
            --customer)
                CUSTOMER_ID="$2"
                shift 2
                ;;
            --secret)
                SECRET_KEY="$2"
                shift 2
                ;;
            --days)
                DURATION_DAYS="$2"
                shift 2
                ;;
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --registry)
                REGISTRY="$2"
                shift 2
                ;;
            --features)
                FEATURES="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                usage
                exit 1
                ;;
        esac
    done
}

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        exit 1
    fi

    # Check required files
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile not found in current directory"
        exit 1
    fi

    if [ ! -f "pyproject.toml" ]; then
        log_error "pyproject.toml not found in current directory"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Generate license and build client image
build_client() {
    if [ -z "$CUSTOMER_ID" ] || [ -z "$SECRET_KEY" ]; then
        log_error "Customer ID and secret key are required for build-client"
        exit 1
    fi

    if [ -z "$IMAGE_TAG" ]; then
        # Generate default tag
        CLEAN_CUSTOMER=$(echo "$CUSTOMER_ID" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
        IMAGE_TAG="llm-firewall:$CLEAN_CUSTOMER"
    fi

    log_info "Building client image for: $CUSTOMER_ID"
    log_info "License duration: $DURATION_DAYS days"
    log_info "Image tag: $IMAGE_TAG"
    log_info "Features: $FEATURES"

    # Ensure secure Dockerfile exists
    if [ ! -f "Dockerfile.client" ]; then
        log_warning "Dockerfile.client not found, using regular Dockerfile (source code will be visible)"
    else
        log_info "Using secure Dockerfile.client (source code protected)"
    fi

    # Build the client image
    FEATURES_ARRAY=$(echo "$FEATURES" | tr ',' ' ')
    python3 build_client_image.py \
        --customer "$CUSTOMER_ID" \
        --tag "$IMAGE_TAG" \
        --secret "$SECRET_KEY" \
        --days "$DURATION_DAYS" \
        --features $FEATURES_ARRAY \
        --compose \
        ${REGISTRY:+--push "$REGISTRY"}

    if [ $? -eq 0 ]; then
        log_success "Client image built successfully: $IMAGE_TAG"
        
        # Create deployment package
        PACKAGE_DIR="client-package-$(echo "$CUSTOMER_ID" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g')"
        mkdir -p "$PACKAGE_DIR"
        
        # Copy files to package
        if [ -f "docker-compose.$(echo "$CUSTOMER_ID" | sed 's/ /_/g').yml" ]; then
            cp "docker-compose.$(echo "$CUSTOMER_ID" | sed 's/ /_/g').yml" "$PACKAGE_DIR/docker-compose.yml"
        fi
        
        if [ -f "client_info_$(echo "$CUSTOMER_ID" | sed 's/ /_/g').json" ]; then
            cp "client_info_$(echo "$CUSTOMER_ID" | sed 's/ /_/g').json" "$PACKAGE_DIR/"
        fi
        
        cp CLIENT_DEPLOYMENT.md "$PACKAGE_DIR/"
        
        # Create README for client
        cat > "$PACKAGE_DIR/README.md" << EOF
# LLM Firewall - Client Package for $CUSTOMER_ID

## Quick Start

1. Create logs directory:
   \`\`\`
   mkdir -p logs
   \`\`\`

2. Start the firewall:
   \`\`\`
   docker-compose up -d
   \`\`\`

3. Test the deployment:
   \`\`\`
   curl http://localhost:5001/health
   \`\`\`

For detailed instructions, see CLIENT_DEPLOYMENT.md

## Package Contents

- \`docker-compose.yml\` - Production deployment configuration
- \`client_info_*.json\` - License and build information
- \`CLIENT_DEPLOYMENT.md\` - Complete deployment guide
- \`README.md\` - This file

## Support

Contact your vendor for support and license renewals.
EOF

        log_success "Client package created: $PACKAGE_DIR"
        
        if [ -n "$REGISTRY" ]; then
            log_success "Image pushed to registry: $REGISTRY/$IMAGE_TAG"
        else
            log_info "To save image to file: docker save $IMAGE_TAG > ${IMAGE_TAG//:/}.tar"
        fi
    else
        log_error "Failed to build client image"
        exit 1
    fi
}

# Deploy locally for development
deploy_local() {
    if [ -z "$SECRET_KEY" ]; then
        log_error "Secret key is required for local deployment"
        exit 1
    fi

    log_info "Deploying LLM Firewall locally..."

    # Check if license exists
    if [ ! -f "license.key" ]; then
        log_warning "No license.key found, generating temporary license..."
        
        # Generate a temporary license for local testing
        python3 generate_license.py \
            --customer "Local Development" \
            --days 30 \
            --secret "$SECRET_KEY" \
            --output "license.key"
    fi

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file..."
        cp .env.example .env
        sed -i.bak "s/your-master-secret-key-here/$SECRET_KEY/" .env
        rm .env.bak
    fi

    # Build and start
    log_info "Building and starting services..."
    export LLM_FIREWALL_SECRET="$SECRET_KEY"
    
    docker-compose up --build -d

    if [ $? -eq 0 ]; then
        log_success "LLM Firewall deployed locally"
        log_info "API available at: http://localhost:5001"
        log_info "Health check: curl http://localhost:5001/health"
        log_info "View logs: docker-compose logs -f"
    else
        log_error "Failed to deploy locally"
        exit 1
    fi
}

# Validate existing license
validate_license() {
    if [ -z "$SECRET_KEY" ]; then
        log_error "Secret key is required for license validation"
        exit 1
    fi

    if [ ! -f "license.key" ]; then
        log_error "license.key file not found"
        exit 1
    fi

    log_info "Validating license..."

    python3 license_manager.py validate \
        --file "license.key" \
        --secret "$SECRET_KEY"

    if [ $? -eq 0 ]; then
        log_success "License validation completed"
    else
        log_error "License validation failed"
        exit 1
    fi
}

# Renew license for existing client
renew_license() {
    if [ -z "$CUSTOMER_ID" ] || [ -z "$SECRET_KEY" ]; then
        log_error "Customer ID and secret key are required for license renewal"
        exit 1
    fi

    log_info "Renewing license for: $CUSTOMER_ID"

    # Generate new license
    python3 generate_license.py \
        --customer "$CUSTOMER_ID" \
        --days "$DURATION_DAYS" \
        --secret "$SECRET_KEY" \
        --output "license_new.key"

    if [ $? -eq 0 ]; then
        log_success "New license generated: license_new.key"
        log_warning "Replace the existing license.key with license_new.key and restart the firewall"
    else
        log_error "Failed to generate new license"
        exit 1
    fi
}

# Main execution
main() {
    parse_args "$@"
    check_prerequisites

    case $ACTION in
        build-client)
            build_client
            ;;
        deploy-local)
            deploy_local
            ;;
        validate)
            validate_license
            ;;
        renew)
            renew_license
            ;;
        *)
            log_error "Unknown command: $ACTION"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"