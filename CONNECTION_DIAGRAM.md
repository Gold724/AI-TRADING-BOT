# 🔗 Connection Diagram - Visual Guide

## 🌐 Complete Infrastructure Map

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   YOUR DEVICES  │    │   CONTABO VPS   │    │  TRADING WORLD  │
│                 │    │  5.189.145.177  │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ 💻 Laptop       │    │ 🐧 Ubuntu 24.04 │    │ 📈 Bulenox      │
│ 📱 Phone        │◄──►│ 🤖 TRAE Bot     │◄──►│ 💰 Live Trading │
│ 🖥️ Desktop      │    │ 🌐 Web Server   │    │ 📊 Market Data  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │ ACCESS  │             │ HOSTING │             │ TRADING │
    │ METHODS │             │ SERVICE │             │ BROKER  │
    └─────────┘             └─────────┘             └─────────┘
```

## 🔌 Access Methods Breakdown

### 1️⃣ SSH Connection (Primary)
```
[Your Device] ──SSH──► [Contabo VPS:18177] ──Commands──► [TRAE Bot]
      │                        │                           │
   Termius App            Ubuntu Shell              systemctl commands
```

### 2️⃣ VNC Connection (GUI Backup)
```
[Your Device] ──VNC──► [Contabo VPS:63162] ──Desktop──► [TRAE Bot]
      │                        │                           │
   VNC Viewer             Ubuntu Desktop            GUI Applications
```

### 3️⃣ Web Interface (Monitoring)
```
[Your Browser] ──HTTP──► [Contabo VPS:5000] ──API──► [TRAE Bot]
      │                         │                      │
   Dashboard UI            Flask Server         Bot Status/Logs
```

---

## 🏗️ Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTABO VPS SERVER                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    SSH      │  │     VNC     │  │     TRAE SERVICES   │ │
│  │   Port      │  │   Port      │  │                     │ │
│  │   18177     │  │   63162     │  │  ┌─────────────────┐ │ │
│  │             │  │             │  │  │   trae-bot      │ │ │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │  │   (systemd)     │ │ │
│  │ │Terminal │ │  │ │Desktop  │ │  │  └─────────────────┘ │ │
│  │ │Access   │ │  │ │GUI      │ │  │  ┌─────────────────┐ │ │
│  │ └─────────┘ │  │ └─────────┘ │  │  │   Flask API     │ │ │
│  └─────────────┘  └─────────────┘  │  │   Port 5000     │ │ │
│                                    │  └─────────────────┘ │ │
│                                    │  ┌─────────────────┐ │ │
│                                    │  │   Playwright    │ │ │
│                                    │  │   Browser       │ │ │
│                                    │  └─────────────────┘ │ │
│                                    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Device-Specific Access

### 🖥️ **From Desktop/Laptop**
```
SSH Client (PuTTY/Terminal)
├── Direct SSH: ssh root@5.189.145.177 -p 18177
├── Termius App: Saved connection profile
└── VNC Viewer: 5.189.145.177:63162

Web Browser
├── TRAE Dashboard: http://5.189.145.177:5000
├── Contabo Panel: https://my.contabo.com
└── VNC Console: Via Contabo web interface
```

### 📱 **From Mobile (Termius)**
```
Termius App
├── SSH Connection: Tap saved server
├── File Manager: Browse VPS files
├── Terminal: Run commands
└── Port Forwarding: Access web services
```

---

## 🔄 Data Flow

### Trading Execution Flow
```
1. Market Signal ──► TRAE Bot ──► Risk Check ──► Bulenox API ──► Trade Executed
                      │              │              │
                   Log Entry    Email Alert    Confirmation
                      │              │              │
                   Database ──► Dashboard ──► Your Phone
```

### Monitoring Flow
```
1. TRAE Bot Status ──► systemd ──► journalctl ──► SSH/VNC ──► Your Device
2. Web Dashboard ──► Flask API ──► HTTP ──► Browser ──► Real-time Updates
3. Email Alerts ──► Gmail SMTP ──► Your Email ──► Mobile Notifications
```

---

## 🚨 Emergency Access Hierarchy

```
┌─ Primary: SSH via Termius
│   ├─ Fast command execution
│   ├─ Mobile access anywhere
│   └─ If fails ──► Try backup
│
├─ Backup: VNC Console
│   ├─ GUI access for complex tasks
│   ├─ Browser testing capability
│   └─ If fails ──► Try emergency
│
└─ Emergency: Contabo Web Console
    ├─ Direct server access
    ├─ Reboot capability
    └─ Always available
```

---

## 🎯 Quick Reference

| Component | Address | Purpose | Access Method |
|-----------|---------|---------|---------------|
| **VPS Server** | 5.189.145.177 | Host everything | SSH/VNC |
| **SSH Service** | :18177 | Command line | Termius/Terminal |
| **VNC Service** | :63162 | GUI desktop | VNC Viewer |
| **TRAE Web UI** | :5000 | Trading dashboard | Web Browser |
| **TRAE Bot** | systemd service | Trading execution | SSH commands |

**Remember**: All roads lead to your TRAE bot running 24/7 on the Contabo VPS, accessible multiple ways for maximum reliability!