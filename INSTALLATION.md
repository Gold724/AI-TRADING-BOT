# AI Trading Sentinel - Installation Guide

## System Requirements

### Required Software

- **Python 3.10+**: The core programming language used by the system
- **Git**: Version control system for code management
- **Google Chrome**: Web browser used for automated trading
- **ChromeDriver**: WebDriver for Chrome automation (matching your Chrome version)

### Required Python Packages

- **selenium**: For browser automation
- **python-dotenv**: For environment variable management
- **requests**: For API communication

## Automated Installation

For your convenience, we've provided an automated installation script that checks for and helps install all required dependencies.

### Windows

1. Double-click the `install_requirements.bat` file
2. Follow the on-screen prompts
3. The script will check for all required software and packages
4. If anything is missing, the script will offer to install it or provide download links

Alternatively, you can run the PowerShell script directly:

```powershell
# Run as administrator for best results
PowerShell.exe -ExecutionPolicy Bypass -File .\install_requirements.ps1
```

### Manual Installation

If you prefer to install the requirements manually, follow these steps:

#### 1. Install Python 3.10+

- Download from [python.org](https://www.python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation
- Verify installation with: `python --version`

#### 2. Install Git

- Download from [git-scm.com](https://git-scm.com/download/win)
- Verify installation with: `git --version`

#### 3. Install Google Chrome

- Download from [google.com/chrome](https://www.google.com/chrome/)

#### 4. Install ChromeDriver

- Download the version matching your Chrome from [Chrome for Testing](https://googlechromelabs.github.io/chrome-for-testing/)
- Extract to the `drivers` directory in this project
- Verify the path: `drivers\chromedriver-win64\chromedriver.exe`

#### 5. Install Python Packages

```bash
pip install selenium python-dotenv requests
```

## Verifying Installation

After installing all requirements, you can verify the installation by running the installation script again. It will check all components and confirm they are properly installed.

## Troubleshooting

### Python Not Found

If you receive "Python not found" errors after installation:
- Ensure Python is added to your PATH
- Try restarting your terminal or computer
- Run `where python` to check if Python is in your PATH

### ChromeDriver Version Mismatch

If you encounter errors about ChromeDriver version not matching Chrome:
- Download the correct ChromeDriver version that matches your Chrome version
- Replace the existing ChromeDriver in the `drivers` directory

### Permission Issues

If you encounter permission errors:
- Run the installation script as Administrator
- Check your system's security settings

## Next Steps

After successfully installing all requirements, you can proceed to configure and run the AI Trading Sentinel system. Refer to the main README.md file for configuration and usage instructions.