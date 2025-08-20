# 🔐 SSH KEY SETUP - Eliminate Password Prompts

## 🎯 GOAL
Setup SSH key authentication to avoid password prompts for VPS access.

---

## 🚀 QUICK SETUP (Windows)

### Step 1: Generate SSH Key (if not exists)
```powershell
# Check if key exists
Test-Path "$env:USERPROFILE\.ssh\id_rsa.pub"

# Generate new key if needed
ssh-keygen -t rsa -b 4096 -C "ai-trading-sentinel@vps"
# Press Enter for default location
# Press Enter for no passphrase (or set one)
```

### Step 2: Copy Public Key to VPS
```powershell
# Display your public key
Get-Content "$env:USERPROFILE\.ssh\id_rsa.pub"
```

### Step 3: Add Key to VPS (via Termius)
```bash
# Connect via Termius first
ssh root@161.97.112.146

# Create .ssh directory if not exists
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key (paste the key from Step 2)
echo "ssh-rsa AAAAB3NzaC1yc2E... your-key-here" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Test: exit and reconnect (should not ask for password)
exit
```

### Step 4: Test Passwordless Connection
```powershell
# Should connect without password prompt
ssh root@161.97.112.146 'echo "SSH Key Auth Working: $(date)"'
```

---

## ✅ SUCCESS INDICATORS
- SSH connects without password prompt
- Commands execute immediately
- No authentication delays

---

**⚠️ SETUP AFTER**: Complete service restart first, then configure SSH keys for future automation.