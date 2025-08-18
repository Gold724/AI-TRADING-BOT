# 🔐 Gmail App Password - Quick Setup (5 Minutes)

## ⚡ Quick Steps

### 1. Enable 2FA (if not done)
- Go to: https://myaccount.google.com/security
- Click "2-Step Verification" → Follow setup

### 2. Generate App Password
- Same page → "App passwords" (at bottom)
- Select "Mail" → "Other (Custom name)"
- Type: `AI Trading Sentinel Bot`
- Click "Generate"
- **Copy the 16-character password** (remove spaces)

### 3. Update .env File
```bash
EMAIL_USERNAME=edufyinc@gmail.com
EMAIL_PASSWORD=abcdefghijklmnop  # Your App Password here
EMAIL_TO=your-alerts@email.com
```

### 4. Test Configuration
```bash
# In VNC terminal or local
python test_email_config.py
```

## 🚨 Common Mistakes

❌ **DON'T USE:**
- Your regular Gmail password
- Password with spaces
- "Less secure app access"

✅ **DO USE:**
- 16-character App Password
- Remove all spaces
- Keep 2FA enabled

## 📱 Mobile Access

If you need to do this on mobile:
1. Open Gmail app → Settings → Account
2. Tap "Manage your Google Account"
3. Security → 2-Step Verification → App passwords

## 🆘 Troubleshooting

**"Authentication failed"**
→ Regenerate App Password

**"No App passwords option"**
→ Enable 2FA first

**"Email not received"**
→ Check spam folder

## ✅ Success Check

You should see:
```
✅ SMTP connection established
✅ SMTP authentication successful
✅ Test email sent successfully!
```

---
**⏱️ Total Time:** ~5 minutes
**🔒 Security:** App Password is safer than regular password
**📧 Result:** Automated trading alerts to your email