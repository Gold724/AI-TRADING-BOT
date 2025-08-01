#!/bin/bash

# AI Trading Sentinel - Requirements Installation Script for Linux/macOS
# This script checks for and installs all required dependencies

# ANSI color codes
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
CYAN="\033[0;36m"
NC="\033[0m" # No Color

# Function to display status messages with colors
function write_status {
    local message="$1"
    local status="$2"
    local color="$3"
    
    echo -e "${color}[${status}]${NC} ${message}"
}

# Function to check Python version
function check_python {
    if command -v python3 &> /dev/null; then
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        python_major=$(echo "$python_version" | cut -d'.' -f1)
        python_minor=$(echo "$python_version" | cut -d'.' -f2)
        
        if [ "$python_major" -ge 3 ] && [ "$python_minor" -ge 10 ]; then
            write_status "Python $python_version installed" "✓" "$GREEN"
            return 0
        else
            write_status "Python $python_version detected, but version 3.10+ is required" "✗" "$RED"
            return 1
        fi
    else
        write_status "Python 3 not found" "✗" "$RED"
        return 1
    fi
}

# Function to check Git installation
function check_git {
    if command -v git &> /dev/null; then
        git_version=$(git --version | cut -d' ' -f3)
        write_status "Git $git_version installed" "✓" "$GREEN"
        return 0
    else
        write_status "Git not found" "✗" "$RED"
        return 1
    fi
}

# Function to check Chrome installation
function check_chrome {
    if command -v google-chrome &> /dev/null; then
        chrome_version=$(google-chrome --version | cut -d' ' -f3)
        write_status "Google Chrome $chrome_version installed" "✓" "$GREEN"
        return 0
    elif command -v google-chrome-stable &> /dev/null; then
        chrome_version=$(google-chrome-stable --version | cut -d' ' -f3)
        write_status "Google Chrome $chrome_version installed" "✓" "$GREEN"
        return 0
    else
        write_status "Google Chrome not found" "✗" "$RED"
        return 1
    fi
}

# Function to check ChromeDriver installation
function check_chromedriver {
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    driver_path="$script_dir/drivers/chromedriver-linux64/chromedriver"
    
    if [ -f "$driver_path" ] && [ -x "$driver_path" ]; then
        driver_version=$($driver_path --version | cut -d' ' -f2)
        write_status "ChromeDriver $driver_version installed" "✓" "$GREEN"
        return 0
    else
        write_status "ChromeDriver not found in drivers directory" "✗" "$RED"
        return 1
    fi
}

# Function to check Python packages
function check_python_packages {
    required_packages=("selenium" "python-dotenv" "requests")
    missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            version=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null)
            write_status "$package $version installed" "✓" "$GREEN"
        else
            write_status "$package not installed" "✗" "$RED"
            missing_packages+=("$package")
        fi
    done
    
    echo "${missing_packages[@]}"
}

# Function to install Python packages
function install_python_packages {
    local packages=($@)
    
    if [ ${#packages[@]} -eq 0 ]; then
        write_status "All required Python packages are already installed" "✓" "$GREEN"
        return
    fi
    
    write_status "Installing missing Python packages: ${packages[*]}" "⚙️" "$CYAN"
    
    pip3 install ${packages[@]}
    if [ $? -eq 0 ]; then
        write_status "Successfully installed Python packages" "✓" "$GREEN"
    else
        write_status "Failed to install Python packages" "✗" "$RED"
    fi
}

# Function to download and install ChromeDriver
function install_chromedriver {
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    drivers_dir="$script_dir/drivers"
    
    # Create drivers directory if it doesn't exist
    mkdir -p "$drivers_dir"
    
    # Get Chrome version
    if command -v google-chrome &> /dev/null; then
        chrome_version=$(google-chrome --version | cut -d' ' -f3 | cut -d'.' -f1)
    elif command -v google-chrome-stable &> /dev/null; then
        chrome_version=$(google-chrome-stable --version | cut -d' ' -f3 | cut -d'.' -f1)
    else
        write_status "Cannot determine Chrome version" "✗" "$RED"
        return 1
    fi
    
    write_status "Downloading ChromeDriver for Chrome version $chrome_version" "⚙️" "$CYAN"
    
    # Determine OS type
    if [[ "$(uname)" == "Darwin" ]]; then
        os_type="mac64"
        chromedriver_dir="chromedriver-mac64"
    else
        os_type="linux64"
        chromedriver_dir="chromedriver-linux64"
    fi
    
    # Download ChromeDriver
    download_url="https://storage.googleapis.com/chrome-for-testing-public/$chrome_version.0.0/$os_type/$chromedriver_dir.zip"
    zip_file="$drivers_dir/$chromedriver_dir.zip"
    
    curl -L -o "$zip_file" "$download_url"
    if [ $? -ne 0 ]; then
        write_status "Failed to download ChromeDriver" "✗" "$RED"
        return 1
    fi
    
    # Extract ChromeDriver
    rm -rf "$drivers_dir/$chromedriver_dir"
    unzip -q "$zip_file" -d "$drivers_dir"
    if [ $? -ne 0 ]; then
        write_status "Failed to extract ChromeDriver" "✗" "$RED"
        return 1
    fi
    
    # Make ChromeDriver executable
    chmod +x "$drivers_dir/$chromedriver_dir/chromedriver"
    
    write_status "ChromeDriver successfully installed" "✓" "$GREEN"
    return 0
}

# Main installation process
echo -e "\n${CYAN}===== AI Trading Sentinel - Requirements Installation =====${NC}\n"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    write_status "This script is not running as root. Some operations may fail." "!" "$YELLOW"
    write_status "Consider running with sudo if you encounter permission issues." "!" "$YELLOW"
    echo ""
fi

# Check Python
python_installed=false
check_python
if [ $? -eq 0 ]; then
    python_installed=true
else
    write_status "Please install Python 3.10 or higher" "!" "$YELLOW"
    if [ -f "/etc/debian_version" ]; then
        write_status "Run: sudo apt update && sudo apt install python3.10 python3-pip" "!" "$YELLOW"
    elif [ -f "/etc/redhat-release" ]; then
        write_status "Run: sudo dnf install python3.10 python3-pip" "!" "$YELLOW"
    elif [[ "$(uname)" == "Darwin" ]]; then
        write_status "Run: brew install python@3.10" "!" "$YELLOW"
    else
        write_status "Visit https://www.python.org/downloads/" "!" "$YELLOW"
    fi
fi

# Check Git
git_installed=false
check_git
if [ $? -eq 0 ]; then
    git_installed=true
else
    write_status "Please install Git" "!" "$YELLOW"
    if [ -f "/etc/debian_version" ]; then
        write_status "Run: sudo apt update && sudo apt install git" "!" "$YELLOW"
    elif [ -f "/etc/redhat-release" ]; then
        write_status "Run: sudo dnf install git" "!" "$YELLOW"
    elif [[ "$(uname)" == "Darwin" ]]; then
        write_status "Run: brew install git" "!" "$YELLOW"
    else
        write_status "Visit https://git-scm.com/downloads" "!" "$YELLOW"
    fi
fi

# Check Chrome
chrome_installed=false
check_chrome
if [ $? -eq 0 ]; then
    chrome_installed=true
else
    write_status "Please install Google Chrome" "!" "$YELLOW"
    if [ -f "/etc/debian_version" ]; then
        write_status "Run: wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && sudo apt install ./google-chrome-stable_current_amd64.deb" "!" "$YELLOW"
    elif [ -f "/etc/redhat-release" ]; then
        write_status "Run: sudo dnf install https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm" "!" "$YELLOW"
    elif [[ "$(uname)" == "Darwin" ]]; then
        write_status "Run: brew install --cask google-chrome" "!" "$YELLOW"
    else
        write_status "Visit https://www.google.com/chrome/" "!" "$YELLOW"
    fi
fi

# Check ChromeDriver
chromedriver_installed=false
check_chromedriver
if [ $? -eq 0 ]; then
    chromedriver_installed=true
elif [ "$chrome_installed" = true ]; then
    read -p "Do you want to download and install ChromeDriver? (y/n): " install_driver
    if [[ "$install_driver" =~ ^[Yy]$ ]]; then
        install_chromedriver
        if [ $? -eq 0 ]; then
            chromedriver_installed=true
        fi
    else
        write_status "Please download ChromeDriver manually from https://googlechromelabs.github.io/chrome-for-testing/" "!" "$YELLOW"
        write_status "Extract it to the 'drivers' directory in this project" "!" "$YELLOW"
    fi
fi

# Check Python packages
if [ "$python_installed" = true ]; then
    missing_packages=($(check_python_packages))
    if [ ${#missing_packages[@]} -gt 0 ]; then
        read -p "Do you want to install missing Python packages? (y/n): " install_packages
        if [[ "$install_packages" =~ ^[Yy]$ ]]; then
            install_python_packages "${missing_packages[@]}"
        fi
    fi
fi

echo -e "\n${CYAN}===== Installation Check Complete =====${NC}\n"

# Final status
if [ "$python_installed" = true ] && [ "$git_installed" = true ] && [ "$chrome_installed" = true ] && [ "$chromedriver_installed" = true ] && [ ${#missing_packages[@]} -eq 0 ]; then
    echo -e "${GREEN}All requirements are installed and ready to use!${NC}"
    echo -e "${GREEN}You can now run the AI Trading Sentinel system.${NC}"
else
    echo -e "${YELLOW}Some requirements are missing. Please install them before running the system.${NC}"
fi

echo ""
read -p "Press Enter to exit"