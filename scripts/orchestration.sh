#!/bin/bash
# Production deployment script for Prefect orchestration
# This script runs both the Prefect server and deployment workers as background services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/venv"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Function to print colored messages
info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# Function to start Prefect server
start_server() {
    local pid_file="$PID_DIR/prefect-server.pid"

    if is_running "$pid_file"; then
        warn "Prefect server is already running (PID: $(cat $pid_file))"
        return 0
    fi

    info "Starting Prefect server..."

    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"

    # Start Prefect server in background
    nohup prefect server start --host 127.0.0.1 --port 4200 \
        > "$LOG_DIR/prefect-server.log" 2>&1 &

    echo $! > "$pid_file"

    # Wait for server to be ready
    info "Waiting for server to start..."
    sleep 5

    if is_running "$pid_file"; then
        info "Prefect server started successfully (PID: $(cat $pid_file))"
        info "UI available at: http://127.0.0.1:4200"
        info "Logs: $LOG_DIR/prefect-server.log"
        return 0
    else
        error "Failed to start Prefect server"
        return 1
    fi
}

# Function to start deployment worker
start_worker() {
    local environment=${1:-dev}
    local pid_file="$PID_DIR/prefect-worker-$environment.pid"

    if is_running "$pid_file"; then
        warn "Prefect worker for $environment is already running (PID: $(cat $pid_file))"
        return 0
    fi

    info "Starting Prefect deployment worker for $environment..."

    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"

    # Start deployment worker in background
    nohup python -m orchestration.deploy --serve --environment "$environment" \
        > "$LOG_DIR/prefect-worker-$environment.log" 2>&1 &

    echo $! > "$pid_file"

    sleep 2

    if is_running "$pid_file"; then
        info "Prefect worker started successfully (PID: $(cat $pid_file))"
        info "Logs: $LOG_DIR/prefect-worker-$environment.log"
        return 0
    else
        error "Failed to start Prefect worker"
        return 1
    fi
}

# Function to stop Prefect server
stop_server() {
    local pid_file="$PID_DIR/prefect-server.pid"

    if ! is_running "$pid_file"; then
        warn "Prefect server is not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    info "Stopping Prefect server (PID: $pid)..."

    kill "$pid" 2>/dev/null || true

    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$pid_file"
            info "Prefect server stopped"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    warn "Force killing Prefect server..."
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$pid_file"
    info "Prefect server stopped"
}

# Function to stop deployment worker
stop_worker() {
    local environment=${1:-dev}
    local pid_file="$PID_DIR/prefect-worker-$environment.pid"

    if ! is_running "$pid_file"; then
        warn "Prefect worker for $environment is not running"
        return 0
    fi

    local pid=$(cat "$pid_file")
    info "Stopping Prefect worker for $environment (PID: $pid)..."

    kill "$pid" 2>/dev/null || true

    # Wait for process to stop
    for i in {1..10}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            rm -f "$pid_file"
            info "Prefect worker stopped"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    warn "Force killing Prefect worker..."
    kill -9 "$pid" 2>/dev/null || true
    rm -f "$pid_file"
    info "Prefect worker stopped"
}

# Function to show status
status() {
    echo ""
    info "=== Prefect Orchestration Status ==="
    echo ""

    # Check server
    local server_pid_file="$PID_DIR/prefect-server.pid"
    if is_running "$server_pid_file"; then
        local pid=$(cat "$server_pid_file")
        echo -e "${GREEN}✓${NC} Prefect Server: Running (PID: $pid)"
        echo "  UI: http://127.0.0.1:4200"
        echo "  Logs: $LOG_DIR/prefect-server.log"
    else
        echo -e "${RED}✗${NC} Prefect Server: Not running"
    fi

    echo ""

    # Check workers
    for env in dev stage prod; do
        local worker_pid_file="$PID_DIR/prefect-worker-$env.pid"
        if is_running "$worker_pid_file"; then
            local pid=$(cat "$worker_pid_file")
            echo -e "${GREEN}✓${NC} Worker ($env): Running (PID: $pid)"
            echo "  Logs: $LOG_DIR/prefect-worker-$env.log"
        else
            echo -e "${RED}✗${NC} Worker ($env): Not running"
        fi
    done

    echo ""
}

# Function to view logs
logs() {
    local service=${1:-server}
    local lines=${2:-50}

    case $service in
        server)
            tail -n "$lines" -f "$LOG_DIR/prefect-server.log"
            ;;
        worker-dev|worker-stage|worker-prod)
            tail -n "$lines" -f "$LOG_DIR/prefect-$service.log"
            ;;
        *)
            error "Unknown service: $service"
            echo "Usage: $0 logs [server|worker-dev|worker-stage|worker-prod] [lines]"
            exit 1
            ;;
    esac
}

# Function to restart services
restart() {
    local environment=${1:-dev}
    info "Restarting Prefect services for $environment..."
    stop_worker "$environment"
    stop_server
    sleep 2
    start_server
    start_worker "$environment"
}

# Main command handler
case "${1:-start}" in
    start)
        ENVIRONMENT=${2:-dev}
        info "Starting Prefect orchestration for $ENVIRONMENT environment..."
        start_server
        start_worker "$ENVIRONMENT"
        echo ""
        status
        ;;

    stop)
        ENVIRONMENT=${2:-dev}
        info "Stopping Prefect orchestration for $ENVIRONMENT environment..."
        stop_worker "$ENVIRONMENT"
        stop_server
        ;;

    restart)
        ENVIRONMENT=${2:-dev}
        restart "$ENVIRONMENT"
        ;;

    status)
        status
        ;;

    logs)
        logs "${2:-server}" "${3:-50}"
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|logs} [environment] [options]"
        echo ""
        echo "Commands:"
        echo "  start [env]          Start Prefect server and worker (default: dev)"
        echo "  stop [env]           Stop Prefect server and worker (default: dev)"
        echo "  restart [env]        Restart services (default: dev)"
        echo "  status               Show status of all services"
        echo "  logs [service] [n]   Tail logs (default: server, 50 lines)"
        echo ""
        echo "Environments: dev, stage, prod"
        echo "Log services: server, worker-dev, worker-stage, worker-prod"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start dev environment"
        echo "  $0 start prod         # Start production environment"
        echo "  $0 status             # Show status"
        echo "  $0 logs worker-dev    # View dev worker logs"
        echo "  $0 stop prod          # Stop production"
        exit 1
        ;;
esac
