#!/bin/bash
# LogBERT AI Agents - Docker Setup Validation
# ===========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

echo "🐳 LogBERT AI Agents - Docker Setup Validation"
echo "=============================================="
echo ""

# Check if Docker is installed
print_info "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker found: $DOCKER_VERSION"
else
    print_error "Docker is not installed!"
    echo ""
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "Or install Docker Engine on Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker daemon is running
print_info "Checking Docker daemon..."
if docker info &> /dev/null; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running!"
    echo ""
    echo "Please start Docker Desktop or the Docker daemon:"
    echo "  - On macOS/Windows: Start Docker Desktop application"
    echo "  - On Linux: sudo systemctl start docker"
    exit 1
fi

# Check if Docker Compose is available
print_info "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose found: $COMPOSE_VERSION"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    print_success "Docker Compose (plugin) found: $COMPOSE_VERSION"
else
    print_warning "Docker Compose not found!"
    echo "You can still use Docker, but orchestration will be limited."
fi

# Check available disk space
print_info "Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
print_info "Available disk space: $AVAILABLE_SPACE"

# Check available RAM
print_info "Checking system resources..."
if command -v free &> /dev/null; then
    AVAILABLE_RAM=$(free -h | awk 'NR==2{printf "%.1fG", $7/1024/1024}')
    print_info "Available RAM: $AVAILABLE_RAM"
elif command -v vm_stat &> /dev/null; then
    # macOS
    FREE_PAGES=$(vm_stat | grep "Pages free" | awk '{print $3}' | sed 's/\.//')
    FREE_RAM=$(echo "$FREE_PAGES * 4096 / 1024 / 1024 / 1024" | bc -l)
    print_info "Available RAM: ${FREE_RAM}G (approximate)"
fi

# Check if ports are available
print_info "Checking port availability..."
for port in 8000 6379; do
    if lsof -i :$port &> /dev/null; then
        print_warning "Port $port is already in use"
    else
        print_success "Port $port is available"
    fi
done

echo ""
print_info "Validation complete!"
echo ""
echo "🚀 Ready to build and run LogBERT AI Agents!"
echo ""
echo "Next steps:"
echo "1. Build the Docker images:"
echo "   ./docker-scripts.sh build"
echo ""
echo "2. Start the services:"
echo "   ./docker-scripts.sh start    # Production mode"
echo "   ./docker-scripts.sh dev      # Development mode"
echo ""
echo "3. Access the application:"
echo "   http://localhost:8000        # API"
echo "   http://localhost:8000/docs   # API Documentation"
echo ""
