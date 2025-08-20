# 🔥 EMERGENCY FIREWALL FIX

## Problem
- VPS works internally: `curl http://localhost/` ✅
- External access fails: `http://161.97.112.146/` ❌ (ERR_CONNECTION_TIMED_OUT)
- **Root Cause**: Port 80 blocked by firewall

## 🚨 URGENT: Type These 4 Commands in Termius

```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw --force enable
sudo systemctl restart nginx
```

## Expected Results
```
Rule added
Rule added (v6)
Rule added
Rule added (v6)
Firewall is active and enabled on system startup
```

## Test After Fix
1. **Browser Test**: `http://161.97.112.146/`
2. **Should Show**: "SSH Fixed: 161.97.112.146"
3. **Bulenox Details**: Trading bot status

## Alternative Commands (if ufw fails)
```bash
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables-save
sudo systemctl restart nginx
```

## Success Signs
- ✅ Browser loads `http://161.97.112.146/`
- ✅ Shows "SSH Fixed: 161.97.112.146"
- ✅ No more ERR_CONNECTION_TIMED_OUT

## Next Steps After Fix
1. Deploy full trading backend
2. Setup systemd services
3. Configure SSL certificates
4. Test live trading integration

---
**TRAE-SentinelOps**: Firewall blocking external access - 4 commands will fix it!