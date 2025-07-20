#!/bin/bash
# LogBERT AI Agents - Docker Build and Management Scripts
# ======================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
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

# Function to build Docker images
build_images() {
    print_info "Building LogBERT AI Agents Docker images..."
    
    # Build production image
    print_info "Building production image..."
    docker build --target production -t logbert-hadoop-rca:latest .
    
    # Build development image
    print_info "Building development image..."
    docker build --target development --build-arg INSTALL_DEV=true -t logbert-hadoop-rca:dev .
    
    print_success "Docker images built successfully!"
}

# Function to start production services
start_production() {
    print_info "Starting LogBERT AI Agents in production mode..."
    docker-compose up -d
    print_success "Production services started!"
    print_info "API available at: http://localhost:8000"
    print_info "API docs available at: http://localhost:8000/docs"
}

# Function to start development services
start_development() {
    print_info "Starting LogBERT AI Agents in development mode..."
    docker-compose -f docker-compose.dev.yml up -d
    print_success "Development services started!"
    print_info "API available at: http://localhost:8000"
    print_info "API docs available at: http://localhost:8000/docs"
}

# Function to stop services
stop_services() {
    print_info "Stopping LogBERT AI Agents services..."
    docker-compose down
    docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
    print_success "Services stopped!"
}

# Function to view logs
view_logs() {
    local service=${1:-logbert-api}
    print_info "Viewing logs for service: $service"
    docker-compose logs -f "$service"
}

# Function to clean up Docker resources
cleanup() {
    print_warning "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker-compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
    docker system prune -f
    print_success "Cleanup completed!"
}

# Function to run tests in container
run_tests() {
    print_info "Running tests in Docker container..."
    docker run --rm -it logbert-hadoop-rca:dev python -m pytest tests/ -v
}

# Function to show usage
usage() {
    echo "LogBERT AI Agents - Docker Management Script"
    echo "=============================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build      Build Docker images"
    echo "  start      Start production services"
    echo "  dev        Start development services"
    echo "  stop       Stop all services"
    echo "  logs       View logs (optionally specify service name)"
    echo "  test       Run tests in container"
    echo "  cleanup    Clean up Docker resources"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build                    # Build all images"
    echo "  $0 start                    # Start production services"
    echo "  $0 dev                      # Start development services"
    echo "  $0 logs logbert-api        # View API logs"
    echo "  $0 stop                     # Stop all services"
    echo ""
}

# Main script logic
case "${1:-help}" in
    build)
        build_images
        ;;
    start)
        start_production
        ;;
    dev)
        start_development
        ;;
    stop)
        stop_services
        ;;
    logs)
        view_logs "$2"
        ;;
    test)
        run_tests
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac
