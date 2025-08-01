#!/bin/bash

# CI/CD Verification Script for AI Trading Sentinel
# This script helps verify and fix common CI/CD setup issues

set -e

# Color codes for terminal output
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${BLUE}=== AI Trading Sentinel - CI/CD Setup Verification ===${NC}"
echo -e "${YELLOW}This script will check and fix common CI/CD setup issues${NC}"
echo

# Check if .github/workflows directory exists
echo -e "${GREEN}[1/7] Checking for .github/workflows directory...${NC}"
if [ ! -d ".github/workflows" ]; then
    echo -e "${RED}❌ .github/workflows directory not found!${NC}"
    echo -e "${YELLOW}Creating directory...${NC}"
    mkdir -p .github/workflows
    echo -e "${GREEN}✅ Created .github/workflows directory${NC}"
else
    echo -e "${GREEN}✅ .github/workflows directory exists${NC}"
fi

# Check if ci_cd_pipeline.yml exists
echo -e "${GREEN}[2/7] Checking for CI/CD workflow file...${NC}"
if [ ! -f ".github/workflows/ci_cd_pipeline.yml" ]; then
    echo -e "${RED}❌ ci_cd_pipeline.yml not found!${NC}"
    echo -e "${YELLOW}Please check if the file exists with a different name or create it.${NC}"
    echo -e "${YELLOW}See CI_CD_TROUBLESHOOTING.md for guidance.${NC}"
else
    echo -e "${GREEN}✅ ci_cd_pipeline.yml exists${NC}"
fi

# Check if .github is in .gitignore
echo -e "${GREEN}[3/7] Checking if .github is in .gitignore...${NC}"
if grep -q "\.github/" .gitignore; then
    echo -e "${RED}❌ .github/ is in .gitignore!${NC}"
    echo -e "${YELLOW}Fixing .gitignore...${NC}"
    # Create a temporary file
    grep -v "\.github/" .gitignore > .gitignore.tmp
    # Add specific exclusion for secrets only
    echo "# Only ignore GitHub secrets, not workflows" >> .gitignore.tmp
    echo ".github/secrets.env" >> .gitignore.tmp
    # Replace original file
    mv .gitignore.tmp .gitignore
    echo -e "${GREEN}✅ Fixed .gitignore${NC}"
else
    echo -e "${GREEN}✅ .github/ is not in .gitignore${NC}"
fi

# Validate YAML syntax
echo -e "${GREEN}[4/7] Validating YAML syntax...${NC}"
if command -v yamllint > /dev/null; then
    if yamllint .github/workflows/ci_cd_pipeline.yml; then
        echo -e "${GREEN}✅ YAML syntax is valid${NC}"
    else
        echo -e "${RED}❌ YAML syntax errors found!${NC}"
        echo -e "${YELLOW}Please fix the errors above.${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ yamllint not installed, skipping syntax validation${NC}"
    echo -e "${YELLOW}Install with: pip install yamllint${NC}"
fi

# Check if workflow file is committed
echo -e "${GREEN}[5/7] Checking if workflow file is committed...${NC}"
if git log -- .github/workflows/ci_cd_pipeline.yml 2>&1 | grep -q "commit"; then
    echo -e "${GREEN}✅ Workflow file is committed${NC}"
else
    echo -e "${RED}❌ Workflow file is not committed!${NC}"
    echo -e "${YELLOW}Committing workflow file...${NC}"
    git add .github/workflows/ci_cd_pipeline.yml
    git commit -m "Add CI/CD workflow file"
    echo -e "${GREEN}✅ Committed workflow file${NC}"
fi

# Check if GitHub secrets are set (can only suggest)
echo -e "${GREEN}[6/7] Checking for GitHub secrets...${NC}"
echo -e "${YELLOW}⚠️ Cannot check GitHub secrets locally${NC}"
echo -e "${YELLOW}Please ensure these secrets are set in your GitHub repository:${NC}"
echo -e "  - CONTABO_VPS_IP"
echo -e "  - CONTABO_VPS_PASSWORD"
echo -e "  - CONTABO_SSH_PORT"

# Offer to push changes
echo -e "${GREEN}[7/7] Checking for unpushed changes...${NC}"
if git status --porcelain | grep -q ""; then
    echo -e "${YELLOW}⚠️ You have uncommitted changes${NC}"
    echo -e "${YELLOW}Consider committing and pushing:${NC}"
    echo -e "  git add ."
    echo -e "  git commit -m \"Fix CI/CD setup\""
    echo -e "  git push origin main"
else
    echo -e "${GREEN}✅ No uncommitted changes${NC}"
    
    # Check for unpushed commits
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -z "$REMOTE" ]; then
        echo -e "${YELLOW}⚠️ No upstream branch set${NC}"
        echo -e "${YELLOW}Set upstream branch with:${NC}"
        echo -e "  git push -u origin main"
    elif [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}⚠️ You have unpushed commits${NC}"
        echo -e "${YELLOW}Push your changes with:${NC}"
        echo -e "  git push origin main"
    else
        echo -e "${GREEN}✅ All changes are pushed${NC}"
    fi
fi

echo -e "${BLUE}=== Verification Complete ===${NC}"
echo -e "${YELLOW}For more detailed troubleshooting, see:${NC}"
echo -e "  CI_CD_TROUBLESHOOTING.md"