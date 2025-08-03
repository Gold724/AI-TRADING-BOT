# Null Byte Detection Tools

This document provides information about the tools created to detect and fix null bytes in Python files for the AI Trading Sentinel project.

## Why Null Bytes Are Problematic

Null bytes (`\x00`) in text files can cause various issues:

- They can break file parsing in many tools and libraries
- They often cause errors with Git operations
- They can lead to unexpected behavior in Python's string handling
- They may cause problems with CI/CD pipelines

## Available Tools

Three tools are provided to help you detect and fix null bytes:

### 1. PowerShell Script (`find_null_bytes.ps1`)

**Usage:**
```powershell
.\find_null_bytes.ps1
```

This script will:
- Scan all Python files in the project (excluding the `venv` directory)
- Identify files containing null bytes
- Offer to fix the files by removing null bytes and creating backups

### 2. Python Script (`find_null_bytes.py`)

**Usage:**
```bash
python find_null_bytes.py [--fix] [--dir DIRECTORY]
```

**Options:**
- `--fix`: Automatically fix files without prompting
- `--dir`: Specify a directory to scan (default: current directory)

This script provides the same functionality as the PowerShell script but works across all platforms (Windows, macOS, Linux).

### 3. Batch Script (`find_null_bytes.bat`)

**Usage:**
```cmd
find_null_bytes.bat [--fix] [--dir DIRECTORY]
```

This is a simple wrapper around the Python script for Windows users who prefer using CMD.

## How to Use

1. If you suspect null byte issues (e.g., Git errors, parsing problems), run one of the scripts
2. Review the list of files with null bytes
3. Choose whether to fix the files when prompted
4. If you choose to fix, backups will be created with the `.backup` extension

## Integration with CI/CD

You can add the Python script to your CI/CD pipeline to prevent files with null bytes from being committed:

```yaml
# Example GitHub Actions step
- name: Check for null bytes
  run: python find_null_bytes.py
  # Will exit with error if null bytes are found
```

## Troubleshooting

If you encounter issues with the scripts:

1. Ensure you have appropriate permissions to read/write files
2. For the PowerShell script, you may need to set the execution policy: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
3. For the Python script, ensure you have Python 3.6+ installed

## Manual Fix

If the automated tools don't work, you can manually fix files with null bytes:

1. Open the file in a hex editor
2. Search for and remove `00` bytes
3. Save the file with the same encoding (preferably UTF-8)