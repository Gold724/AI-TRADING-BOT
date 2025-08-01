#!/bin/bash
# AI Trading Sentinel Launcher with Auto-Update Support
# This script launches the AI Trading Sentinel with support for automatic GitHub updates

# ANSI color codes
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color

echo -e "${CYAN}AI Trading Sentinel Launcher${NC}"
echo -e "${CYAN}==========================${NC}"

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}Created logs directory${NC}"
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed or not in your PATH${NC}"
    echo -e "${YELLOW}Please install Python 3 using your package manager${NC}"
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}Using $PYTHON_VERSION${NC}"

# Check if the .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Running heartbeat.py to create a default one...${NC}"
    python3 -c "import heartbeat; print('Default .env file created')"
    
    if [ -f ".env" ]; then
        echo -e "${GREEN}Default .env file created. Please edit it with your settings before continuing.${NC}"
        read -p "Press Enter to open the .env file for editing..."
        
        # Try to open with different editors based on availability
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        elif command -v vi &> /dev/null; then
            vi .env
        else
            echo -e "${YELLOW}No text editor found. Please edit the .env file manually.${NC}"
            cat .env
        fi
        
        echo -e "\nAfter saving your changes, press Enter to continue..."
        read
    else
        echo -e "${RED}Failed to create .env file${NC}"
        exit 1
    fi
fi

# Check if GitHub integration is configured
if grep -q "GITHUB_USERNAME=your-username" .env; then
    echo -e "\n${YELLOW}GitHub integration is not configured in your .env file${NC}"
    read -p "Do you want to configure GitHub integration now? (y/n): " configure_github
    
    if [ "$configure_github" = "y" ]; then
        read -p "Enter your GitHub username: " github_username
        read -p "Enter your GitHub Personal Access Token: " github_pat
        read -p "Enter your GitHub repository name (default: ai-trading-sentinel): " github_repo
        
        if [ -z "$github_repo" ]; then
            github_repo="ai-trading-sentinel"
        fi
        
        # Update the .env file
        sed -i "s/GITHUB_USERNAME=your-username/GITHUB_USERNAME=$github_username/" .env
        sed -i "s/GITHUB_PAT=your-personal-access-token/GITHUB_PAT=$github_pat/" .env
        sed -i "s/GITHUB_REPO=ai-trading-sentinel/GITHUB_REPO=$github_repo/" .env
        
        # Ask about auto-update
        read -p "Enable automatic GitHub updates? (y/n): " auto_update
        if [ "$auto_update" = "y" ]; then
            sed -i "s/AUTO_UPDATE_GITHUB=false/AUTO_UPDATE_GITHUB=true/" .env
            
            # Ask about auto-restart
            read -p "Enable automatic restart after updates? (y/n): " auto_restart
            if [ "$auto_restart" = "y" ]; then
                sed -i "s/RESTART_AFTER_UPDATE=false/RESTART_AFTER_UPDATE=true/" .env
            fi
        fi
        
        echo -e "${GREEN}GitHub integration configured successfully${NC}"
    fi
fi

# Ask about debug mode
read -p "\nEnable debug mode? (y/n): " debug_mode
debug_arg=""
if [ "$debug_mode" = "y" ]; then
    debug_arg="--debug"
    echo -e "${YELLOW}Debug mode enabled${NC}"
fi

# Make the script executable if it isn't already
if [ ! -x "start_sentinel_with_autoupdate.py" ]; then
    chmod +x start_sentinel_with_autoupdate.py
fi

# Start the sentinel with auto-update support
echo -e "\n${CYAN}Starting AI Trading Sentinel with auto-update support...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the sentinel${NC}\n"

try_python() {
    if command -v "$1" &> /dev/null; then
        "$1" start_sentinel_with_autoupdate.py $debug_arg
        return 0
    fi
    return 1
}

# Try different Python commands
if ! try_python "python3"; then
    if ! try_python "python"; then
        echo -e "${RED}Failed to start the sentinel. No Python interpreter found.${NC}"
        exit 1
    fi
fi