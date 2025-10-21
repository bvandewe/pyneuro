#!/bin/bash

# 🍕 Mario's Pizzeria Docker Management Script
#
# This script provides easy commands to manage the Mario's Pizzeria Docker environment
# Usage: ./mario-docker.sh [command]
#
# Commands:
#   start     - Start all services
#   stop      - Stop all services
#   restart   - Restart all services
#   logs      - View logs for all services
#   status    - Check status of all services
#   clean     - Stop and remove all data (destructive!)
#   reset     - Complete reset and rebuild
#   help      - Show this help message

set -e

COMPOSE_FILE="docker-compose.mario.yml"
PROJECT_NAME="mario-pizzeria"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Emoji constants
PIZZA="🍕"
ROCKET="🚀"
STOP="🛑"
CLEAN="🧹"
LOGS="📜"
STATUS="📊"
HELP="❓"
SUCCESS="✅"
WARNING="⚠️"
ERROR="❌"

print_header() {
    echo -e "${BLUE}${PIZZA} Mario's Pizzeria Docker Manager ${PIZZA}${NC}"
    echo -e "${BLUE}======================================${NC}"
}

print_success() {
    echo -e "${GREEN}${SUCCESS} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_error() {
    echo -e "${RED}${ERROR} $1${NC}"
}

print_info() {
    echo -e "${CYAN}$1${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

start_services() {
    print_header
    print_info "${ROCKET} Starting Mario's Pizzeria services..."

    echo -e "${CYAN}Building and starting containers...${NC}"
    docker-compose -f $COMPOSE_FILE up -d --build

    echo ""
    print_info "⏳ Waiting for services to be ready..."
    sleep 5

    echo ""
    print_success "Mario's Pizzeria is starting up!"
    print_info ""
    print_info "🌐 Access your services at:"
    print_info "  ${PIZZA} Mario's Pizzeria UI: http://localhost:8080/ui"
    print_info "  ${PIZZA} Mario's Pizzeria API: http://localhost:8080/api/docs"
    print_info "  🗄️  MongoDB Express:      http://localhost:8081 (admin/admin123)"
    print_info "  🎪 EventStoreDB:         http://localhost:2113"
    print_info "  🎬 Event Player:         http://localhost:8085"
    print_info "  🔐 Keycloak Admin:       http://localhost:8090/admin (admin/admin)"
    print_info ""
    print_info "📚 Check the logs with: ./mario-docker.sh logs"
    print_info "📊 Check the status with: ./mario-docker.sh status"
}

stop_services() {
    print_header
    print_info "${STOP} Stopping Mario's Pizzeria services..."

    docker-compose -f $COMPOSE_FILE down

    print_success "Mario's Pizzeria services stopped!"
}

restart_services() {
    print_header
    print_info "${ROCKET} Restarting Mario's Pizzeria services..."

    docker-compose -f $COMPOSE_FILE restart

    print_success "Mario's Pizzeria services restarted!"
}

show_logs() {
    print_header
    print_info "${LOGS} Showing logs for Mario's Pizzeria services..."
    print_info "Press Ctrl+C to exit log view"
    echo ""

    docker-compose -f $COMPOSE_FILE logs -f
}

show_status() {
    print_header
    print_info "${STATUS} Mario's Pizzeria Services Status:"
    echo ""

    docker-compose -f $COMPOSE_FILE ps

    echo ""
    print_info "🔍 Quick Health Checks:"

    # Check Mario's Pizzeria API
    if curl -s http://localhost:8080/health &> /dev/null; then
        print_success "Mario's Pizzeria API is responding"
    else
        print_warning "Mario's Pizzeria API is not responding"
    fi

    # Check MongoDB
    if docker-compose -f $COMPOSE_FILE exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" &> /dev/null; then
        print_success "MongoDB is responding"
    else
        print_warning "MongoDB is not responding"
    fi

    # Check Keycloak
    if curl -s http://localhost:8090/health/ready &> /dev/null; then
        print_success "Keycloak is responding"
    else
        print_warning "Keycloak is not responding (may still be starting up)"
    fi
}

clean_environment() {
    print_header
    print_warning "This will stop all services and REMOVE ALL DATA!"
    print_warning "This action cannot be undone."

    read -p "Are you sure? Type 'yes' to continue: " -r
    if [[ $REPLY != "yes" ]]; then
        print_info "Operation cancelled."
        exit 0
    fi

    print_info "${CLEAN} Cleaning Mario's Pizzeria environment..."

    docker-compose -f $COMPOSE_FILE down -v --remove-orphans

    print_success "Mario's Pizzeria environment cleaned!"
    print_info "All data has been removed. Run './mario-docker.sh start' to create a fresh environment."
}

reset_environment() {
    print_header
    print_warning "This will completely reset Mario's Pizzeria environment!"
    print_warning "All containers, images, and data will be removed and rebuilt."

    read -p "Are you sure? Type 'yes' to continue: " -r
    if [[ $REPLY != "yes" ]]; then
        print_info "Operation cancelled."
        exit 0
    fi

    print_info "${CLEAN} Resetting Mario's Pizzeria environment..."

    docker-compose -f $COMPOSE_FILE down -v --rmi all --remove-orphans
    docker system prune -f

    print_info "${ROCKET} Rebuilding Mario's Pizzeria environment..."
    docker-compose -f $COMPOSE_FILE up -d --build

    print_success "Mario's Pizzeria environment reset and rebuilt!"
}

show_help() {
    print_header
    echo ""
    echo -e "${CYAN}Usage: ./mario-docker.sh [command]${NC}"
    echo ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  ${GREEN}start${NC}     - Start all Mario's Pizzeria services"
    echo -e "  ${GREEN}stop${NC}      - Stop all services"
    echo -e "  ${GREEN}restart${NC}   - Restart all services"
    echo -e "  ${GREEN}logs${NC}      - View logs for all services (follow mode)"
    echo -e "  ${GREEN}status${NC}    - Check status and health of all services"
    echo -e "  ${RED}clean${NC}     - Stop and remove all data (destructive!)"
    echo -e "  ${RED}reset${NC}     - Complete reset and rebuild (destructive!)"
    echo -e "  ${GREEN}help${NC}      - Show this help message"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  ./mario-docker.sh start   ${CYAN}# Start the pizzeria${NC}"
    echo -e "  ./mario-docker.sh logs    ${CYAN}# Watch the logs${NC}"
    echo -e "  ./mario-docker.sh status  ${CYAN}# Check if everything is running${NC}"
    echo ""
    echo -e "${YELLOW}Services included:${NC}"
    echo -e "  ${PIZZA} Mario's Pizzeria API (FastAPI + Neuroglia)"
    echo -e "  🗄️  MongoDB + MongoDB Express"
    echo -e "  🎪 EventStoreDB"
    echo -e "  🎬 Event Player"
    echo -e "  🔐 Keycloak + PostgreSQL"
    echo ""
}

# Check if Docker is available
check_docker

# Handle commands
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    clean)
        clean_environment
        ;;
    reset)
        reset_environment
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
