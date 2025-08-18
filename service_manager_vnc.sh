#!/bin/bash

# AI Trading Sentinel - VNC Service Manager
# GUI-based service management for VNC environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="trae-bot"
PROJECT_DIR="$HOME/ai-trading-sentinel"
LOG_FILE="$PROJECT_DIR/logs/trae.log"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

echo -e "${BLUE}🚀 AI Trading Sentinel - VNC Service Manager${NC}"
echo -e "${BLUE}=============================================${NC}"
echo ""

# Function to show notification
show_notification() {
    local message="$1"
    local type="$2"
    
    if command -v notify-send &> /dev/null; then
        case $type in
            "success")
                notify-send "Trading Bot" "$message" --icon=dialog-information --urgency=normal
                ;;
            "warning")
                notify-send "Trading Bot" "$message" --icon=dialog-warning --urgency=normal
                ;;
            "error")
                notify-send "Trading Bot" "$message" --icon=dialog-error --urgency=critical
                ;;
            *)
                notify-send "Trading Bot" "$message" --icon=dialog-information --urgency=low
                ;;
        esac
    fi
    
    case $type in
        "success")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "info")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "progress")
            echo -e "${CYAN}🔄 $message${NC}"
            ;;
        *)
            echo -e "${PURPLE}📋 $message${NC}"
            ;;
    esac
}

# Check service status
check_service_status() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "active"
    elif systemctl is-enabled --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo "inactive"
    else
        echo "disabled"
    fi
}

# Get service status with details
get_service_details() {
    local status=$(check_service_status)
    local uptime="N/A"
    local memory="N/A"
    local cpu="N/A"
    
    if [ "$status" = "active" ]; then
        # Get uptime
        uptime=$(systemctl show "$SERVICE_NAME" --property=ActiveEnterTimestamp --value)
        if [ -n "$uptime" ] && [ "$uptime" != "" ]; then
            uptime=$(date -d "$uptime" '+%Y-%m-%d %H:%M:%S')
        fi
        
        # Get memory usage
        local pid=$(systemctl show "$SERVICE_NAME" --property=MainPID --value)
        if [ -n "$pid" ] && [ "$pid" != "0" ]; then
            memory=$(ps -p "$pid" -o rss= 2>/dev/null | awk '{print int($1/1024)"MB"}' || echo "N/A")
            cpu=$(ps -p "$pid" -o %cpu= 2>/dev/null | awk '{print $1"%"}' || echo "N/A")
        fi
    fi
    
    echo "Status: $status"
    echo "Uptime: $uptime"
    echo "Memory: $memory"
    echo "CPU: $cpu"
}

# Display service status in GUI
show_service_status() {
    local details=$(get_service_details)
    local status=$(check_service_status)
    
    show_notification "Service Status: $status" "info"
    echo -e "${CYAN}📊 Service Details:${NC}"
    echo "$details"
    echo ""
    
    # Show in GUI if available
    if command -v zenity &> /dev/null; then
        zenity --info --title="Trading Bot Status" --text="$details" --width=400 --height=200 &
    fi
}

# Start the service
start_service() {
    show_notification "Starting $SERVICE_NAME service..." "progress"
    
    if sudo systemctl start "$SERVICE_NAME"; then
        sleep 3  # Wait for service to initialize
        
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            show_notification "✅ Service started successfully!" "success"
            
            # Enable auto-start
            sudo systemctl enable "$SERVICE_NAME"
            show_notification "Service enabled for auto-start" "success"
            
            return 0
        else
            show_notification "Service failed to start properly" "error"
            return 1
        fi
    else
        show_notification "Failed to start service" "error"
        return 1
    fi
}

# Stop the service
stop_service() {
    show_notification "Stopping $SERVICE_NAME service..." "progress"
    
    if sudo systemctl stop "$SERVICE_NAME"; then
        show_notification "Service stopped successfully" "success"
        return 0
    else
        show_notification "Failed to stop service" "error"
        return 1
    fi
}

# Restart the service
restart_service() {
    show_notification "Restarting $SERVICE_NAME service..." "progress"
    
    if sudo systemctl restart "$SERVICE_NAME"; then
        sleep 3
        if systemctl is-active --quiet "$SERVICE_NAME"; then
            show_notification "Service restarted successfully!" "success"
            return 0
        else
            show_notification "Service failed to restart properly" "error"
            return 1
        fi
    else
        show_notification "Failed to restart service" "error"
        return 1
    fi
}

# View service logs
view_logs() {
    local log_choice="recent"
    
    if command -v zenity &> /dev/null; then
        log_choice=$(zenity --list --title="View Logs" --text="Select log view option:" \
            --column="Option" --column="Description" \
            "recent" "Last 50 lines" \
            "follow" "Follow live logs" \
            "full" "Full log file" \
            "errors" "Error logs only" \
            --width=400 --height=300)
    fi
    
    case $log_choice in
        "recent")
            show_notification "Showing recent logs..." "info"
            if [ -f "$LOG_FILE" ]; then
                tail -n 50 "$LOG_FILE" | zenity --text-info --title="Recent Logs" --width=800 --height=600 &
            fi
            sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager
            ;;
        "follow")
            show_notification "Following live logs (Ctrl+C to stop)..." "info"
            gnome-terminal -- bash -c "sudo journalctl -u $SERVICE_NAME -f; read -p 'Press Enter to close...'"
            ;;
        "full")
            show_notification "Opening full log file..." "info"
            if [ -f "$LOG_FILE" ]; then
                gedit "$LOG_FILE" &
            fi
            gnome-terminal -- bash -c "sudo journalctl -u $SERVICE_NAME --no-pager | less; read -p 'Press Enter to close...'"
            ;;
        "errors")
            show_notification "Showing error logs..." "info"
            sudo journalctl -u "$SERVICE_NAME" -p err --no-pager
            ;;
        *)
            show_notification "Showing recent logs..." "info"
            sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
            ;;
    esac
}

# Monitor service in real-time
monitor_service() {
    show_notification "Opening service monitor..." "info"
    
    # Create monitoring script
    local monitor_script="/tmp/service_monitor.sh"
    cat > "$monitor_script" << 'EOF'
#!/bin/bash
SERVICE_NAME="trae-bot"
while true; do
    clear
    echo "=== AI Trading Sentinel - Service Monitor ==="
    echo "Time: $(date)"
    echo ""
    
    # Service status
    echo "🔍 Service Status:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    
    # Resource usage
    echo "📊 Resource Usage:"
    local pid=$(systemctl show "$SERVICE_NAME" --property=MainPID --value)
    if [ -n "$pid" ] && [ "$pid" != "0" ]; then
        ps -p "$pid" -o pid,ppid,%cpu,%mem,etime,cmd 2>/dev/null || echo "Process not found"
    else
        echo "Service not running"
    fi
    echo ""
    
    # Recent logs
    echo "📋 Recent Logs (last 5 lines):"
    journalctl -u "$SERVICE_NAME" -n 5 --no-pager
    echo ""
    echo "Press Ctrl+C to exit monitor"
    
    sleep 5
done
EOF
    
    chmod +x "$monitor_script"
    gnome-terminal -- bash -c "$monitor_script"
}

# Open system monitor
open_system_monitor() {
    show_notification "Opening system monitor..." "info"
    
    if command -v gnome-system-monitor &> /dev/null; then
        gnome-system-monitor &
    elif command -v htop &> /dev/null; then
        gnome-terminal -- htop
    else
        gnome-terminal -- top
    fi
}

# Service troubleshooting
troubleshoot_service() {
    show_notification "Running service diagnostics..." "progress"
    
    local issues=0
    local report="/tmp/service_diagnostics.txt"
    
    echo "AI Trading Sentinel - Service Diagnostics Report" > "$report"
    echo "Generated: $(date)" >> "$report"
    echo "========================================" >> "$report"
    echo "" >> "$report"
    
    # Check service file
    echo "1. Service File Check:" >> "$report"
    if [ -f "$SERVICE_FILE" ]; then
        echo "   ✅ Service file exists: $SERVICE_FILE" >> "$report"
    else
        echo "   ❌ Service file missing: $SERVICE_FILE" >> "$report"
        ((issues++))
    fi
    echo "" >> "$report"
    
    # Check project directory
    echo "2. Project Directory Check:" >> "$report"
    if [ -d "$PROJECT_DIR" ]; then
        echo "   ✅ Project directory exists: $PROJECT_DIR" >> "$report"
        if [ -f "$PROJECT_DIR/main.py" ]; then
            echo "   ✅ main.py found" >> "$report"
        else
            echo "   ❌ main.py missing" >> "$report"
            ((issues++))
        fi
    else
        echo "   ❌ Project directory missing: $PROJECT_DIR" >> "$report"
        ((issues++))
    fi
    echo "" >> "$report"
    
    # Check .env file
    echo "3. Environment Configuration:" >> "$report"
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo "   ✅ .env file exists" >> "$report"
        local env_issues=$(grep -c "your_" "$PROJECT_DIR/.env" 2>/dev/null || echo "0")
        if [ "$env_issues" -gt 0 ]; then
            echo "   ⚠️  $env_issues placeholder values found in .env" >> "$report"
        fi
    else
        echo "   ❌ .env file missing" >> "$report"
        ((issues++))
    fi
    echo "" >> "$report"
    
    # Check logs directory
    echo "4. Logs Directory:" >> "$report"
    if [ -d "$PROJECT_DIR/logs" ]; then
        echo "   ✅ Logs directory exists" >> "$report"
        if [ -f "$LOG_FILE" ]; then
            echo "   ✅ Log file exists" >> "$report"
            local log_size=$(du -h "$LOG_FILE" 2>/dev/null | cut -f1 || echo "0")
            echo "   📊 Log file size: $log_size" >> "$report"
        else
            echo "   ⚠️  Log file missing" >> "$report"
        fi
    else
        echo "   ❌ Logs directory missing" >> "$report"
        ((issues++))
    fi
    echo "" >> "$report"
    
    # Check Python environment
    echo "5. Python Environment:" >> "$report"
    if command -v python3 &> /dev/null; then
        echo "   ✅ Python3 available: $(python3 --version)" >> "$report"
        if python3 -c "import playwright" 2>/dev/null; then
            echo "   ✅ Playwright installed" >> "$report"
        else
            echo "   ❌ Playwright not installed" >> "$report"
            ((issues++))
        fi
    else
        echo "   ❌ Python3 not found" >> "$report"
        ((issues++))
    fi
    echo "" >> "$report"
    
    # Service status
    echo "6. Service Status:" >> "$report"
    local status=$(check_service_status)
    echo "   Status: $status" >> "$report"
    if [ "$status" != "active" ]; then
        echo "   Recent errors:" >> "$report"
        sudo journalctl -u "$SERVICE_NAME" -p err -n 5 --no-pager >> "$report" 2>/dev/null || echo "   No recent errors found" >> "$report"
    fi
    echo "" >> "$report"
    
    # Summary
    echo "========================================" >> "$report"
    echo "SUMMARY:" >> "$report"
    if [ $issues -eq 0 ]; then
        echo "✅ No critical issues found" >> "$report"
        show_notification "Diagnostics complete - no critical issues found" "success"
    else
        echo "❌ $issues critical issues found" >> "$report"
        show_notification "Diagnostics complete - $issues issues found" "warning"
    fi
    
    # Show report
    gedit "$report" &
    cat "$report"
}

# Main menu
show_main_menu() {
    if command -v zenity &> /dev/null; then
        local choice=$(zenity --list --title="AI Trading Sentinel - Service Manager" \
            --text="Select an action:" --width=500 --height=400 \
            --column="Action" --column="Description" \
            "status" "Show service status" \
            "start" "Start the service" \
            "stop" "Stop the service" \
            "restart" "Restart the service" \
            "logs" "View service logs" \
            "monitor" "Real-time monitoring" \
            "system" "Open system monitor" \
            "troubleshoot" "Run diagnostics" \
            "exit" "Exit manager")
        
        case $choice in
            "status")
                show_service_status
                ;;
            "start")
                start_service
                ;;
            "stop")
                stop_service
                ;;
            "restart")
                restart_service
                ;;
            "logs")
                view_logs
                ;;
            "monitor")
                monitor_service
                ;;
            "system")
                open_system_monitor
                ;;
            "troubleshoot")
                troubleshoot_service
                ;;
            "exit")
                show_notification "Exiting service manager" "info"
                exit 0
                ;;
            *)
                show_notification "Invalid selection" "warning"
                ;;
        esac
    else
        # Fallback text menu
        echo -e "${CYAN}Select an action:${NC}"
        echo "1. Show service status"
        echo "2. Start service"
        echo "3. Stop service"
        echo "4. Restart service"
        echo "5. View logs"
        echo "6. Monitor service"
        echo "7. Run diagnostics"
        echo "8. Exit"
        
        read -p "Enter choice (1-8): " choice
        
        case $choice in
            1) show_service_status ;;
            2) start_service ;;
            3) stop_service ;;
            4) restart_service ;;
            5) view_logs ;;
            6) monitor_service ;;
            7) troubleshoot_service ;;
            8) exit 0 ;;
            *) show_notification "Invalid choice" "warning" ;;
        esac
    fi
}

# Quick status check
quick_status() {
    local status=$(check_service_status)
    show_notification "Service Status: $status" "info"
    
    case $status in
        "active")
            show_notification "✅ Trading bot is running" "success"
            ;;
        "inactive")
            show_notification "⚠️  Trading bot is stopped" "warning"
            ;;
        "disabled")
            show_notification "❌ Trading bot service is disabled" "error"
            ;;
    esac
}

# Main execution
main() {
    # Check if running with arguments
    case "${1:-}" in
        "status")
            quick_status
            ;;
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "logs")
            view_logs
            ;;
        "monitor")
            monitor_service
            ;;
        "troubleshoot")
            troubleshoot_service
            ;;
        "")
            # Interactive mode
            while true; do
                show_main_menu
                echo ""
                read -p "Press Enter to continue or Ctrl+C to exit..."
            done
            ;;
        *)
            echo "Usage: $0 [status|start|stop|restart|logs|monitor|troubleshoot]"
            echo "Run without arguments for interactive mode"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"