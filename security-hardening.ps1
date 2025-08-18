# TradeBot Sentinel - Security Hardening Script (PowerShell)
# This script implements comprehensive security measures for Windows cloud deployment

param(
    [string]$Action = "install",
    [string]$SSHPort = "2222",
    [string]$VPNClientName = "",
    [string]$AllowedIP = ""
)

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$Config = @{
    SSHPort = $SSHPort
    VPNPort = "1194"
    LogPath = "C:\TradeBot\Logs\security.log"
    ConfigPath = "C:\TradeBot\Config"
    VPNPath = "C:\TradeBot\VPN"
    SSHKeyPath = "C:\TradeBot\SSH"
    AllowedIPsFile = "C:\TradeBot\Config\allowed_ips.txt"
}

# Ensure directories exist
$Config.Values | ForEach-Object {
    $dir = Split-Path $_ -Parent
    if ($dir -and !(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage -ForegroundColor White }
    }
    
    Add-Content -Path $Config.LogPath -Value $logMessage
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Install-RequiredModules {
    Write-Log "Installing required PowerShell modules..."
    
    $modules = @(
        "Posh-SSH",
        "PowerShellGet",
        "PackageManagement",
        "PSWindowsUpdate",
        "Carbon"
    )
    
    foreach ($module in $modules) {
        try {
            if (!(Get-Module -ListAvailable -Name $module)) {
                Write-Log "Installing module: $module"
                Install-Module -Name $module -Force -AllowClobber -Scope AllUsers
            } else {
                Write-Log "Module already installed: $module"
            }
        } catch {
            Write-Log "Failed to install module $module`: $($_.Exception.Message)" "ERROR"
        }
    }
}

function Enable-WindowsFeatures {
    Write-Log "Enabling required Windows features..."
    
    $features = @(
        "IIS-WebServerRole",
        "IIS-WebServer",
        "IIS-CommonHttpFeatures",
        "IIS-HttpErrors",
        "IIS-HttpLogging",
        "IIS-Security",
        "IIS-RequestFiltering",
        "IIS-IPSecurity",
        "Microsoft-Windows-Subsystem-Linux"
    )
    
    foreach ($feature in $features) {
        try {
            $featureState = Get-WindowsOptionalFeature -Online -FeatureName $feature -ErrorAction SilentlyContinue
            if ($featureState -and $featureState.State -eq "Disabled") {
                Write-Log "Enabling feature: $feature"
                Enable-WindowsOptionalFeature -Online -FeatureName $feature -All -NoRestart
            }
        } catch {
            Write-Log "Feature not available or already enabled: $feature" "WARNING"
        }
    }
}

function Install-OpenSSH {
    Write-Log "Installing and configuring OpenSSH Server..."
    
    # Install OpenSSH Server
    $sshFeature = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
    if ($sshFeature.State -ne "Installed") {
        Add-WindowsCapability -Online -Name $sshFeature.Name
    }
    
    # Start and enable SSH service
    Start-Service sshd
    Set-Service -Name sshd -StartupType 'Automatic'
    
    # Configure SSH
    $sshConfig = @"
# TradeBot Sentinel SSH Configuration
Port $($Config.SSHPort)
Protocol 2
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
PrintMotd no
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
LoginGraceTime 30
Banner C:\TradeBot\Config\ssh_banner.txt
"@
    
    $sshConfigPath = "$env:ProgramData\ssh\sshd_config"
    Set-Content -Path $sshConfigPath -Value $sshConfig
    
    # Create SSH banner
    $banner = @"
***************************************************************************
                    AUTHORIZED ACCESS ONLY
                   TradeBot Sentinel System
***************************************************************************

This system is for authorized users only. All activities are monitored
and logged. Unauthorized access is strictly prohibited and will be
prosecuted to the full extent of the law.

***************************************************************************
"@
    
    Set-Content -Path "C:\TradeBot\Config\ssh_banner.txt" -Value $banner
    
    # Restart SSH service
    Restart-Service sshd
    
    Write-Log "OpenSSH Server configured on port $($Config.SSHPort)" "SUCCESS"
}

function Configure-WindowsFirewall {
    Write-Log "Configuring Windows Firewall..."
    
    # Enable Windows Firewall for all profiles
    Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True
    
    # Remove existing rules for our services
    Get-NetFirewallRule -DisplayName "TradeBot*" | Remove-NetFirewallRule -ErrorAction SilentlyContinue
    
    # Allow SSH on custom port
    New-NetFirewallRule -DisplayName "TradeBot SSH" -Direction Inbound -Protocol TCP -LocalPort $Config.SSHPort -Action Allow
    
    # Allow HTTP/HTTPS
    New-NetFirewallRule -DisplayName "TradeBot HTTP" -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
    New-NetFirewallRule -DisplayName "TradeBot HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
    
    # Allow monitoring ports
    New-NetFirewallRule -DisplayName "TradeBot Grafana" -Direction Inbound -Protocol TCP -LocalPort 3000 -Action Allow
    New-NetFirewallRule -DisplayName "TradeBot Prometheus" -Direction Inbound -Protocol TCP -LocalPort 9090 -Action Allow
    New-NetFirewallRule -DisplayName "TradeBot Alertmanager" -Direction Inbound -Protocol TCP -LocalPort 9093 -Action Allow
    New-NetFirewallRule -DisplayName "TradeBot Loki" -Direction Inbound -Protocol TCP -LocalPort 3100 -Action Allow
    
    # Allow VPN
    New-NetFirewallRule -DisplayName "TradeBot OpenVPN" -Direction Inbound -Protocol UDP -LocalPort $Config.VPNPort -Action Allow
    
    # Block all other inbound traffic
    Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultInboundAction Block
    Set-NetFirewallProfile -Profile Domain,Public,Private -DefaultOutboundAction Allow
    
    Write-Log "Windows Firewall configured successfully" "SUCCESS"
}

function Install-FailToBan {
    Write-Log "Installing Fail2Ban equivalent (WinSSHD)..."
    
    # Create a PowerShell script to monitor failed login attempts
    $fail2banScript = @'
# TradeBot Sentinel - Failed Login Monitor
param([int]$MaxAttempts = 5, [int]$BanTimeMinutes = 60)

$logPath = "C:\TradeBot\Logs\failed_logins.log"
$bannedIPsPath = "C:\TradeBot\Config\banned_ips.txt"

# Get failed login events from the last hour
$events = Get-WinEvent -FilterHashtable @{LogName="Security"; ID=4625; StartTime=(Get-Date).AddHours(-1)} -ErrorAction SilentlyContinue

$failedAttempts = @{}
foreach ($event in $events) {
    $xml = [xml]$event.ToXml()
    $sourceIP = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "IpAddress"} | Select-Object -ExpandProperty "#text"
    
    if ($sourceIP -and $sourceIP -ne "-" -and $sourceIP -ne "127.0.0.1") {
        if ($failedAttempts.ContainsKey($sourceIP)) {
            $failedAttempts[$sourceIP]++
        } else {
            $failedAttempts[$sourceIP] = 1
        }
    }
}

# Ban IPs with too many failed attempts
foreach ($ip in $failedAttempts.Keys) {
    if ($failedAttempts[$ip] -ge $MaxAttempts) {
        # Check if already banned
        $existingRule = Get-NetFirewallRule -DisplayName "Ban-$ip" -ErrorAction SilentlyContinue
        if (-not $existingRule) {
            New-NetFirewallRule -DisplayName "Ban-$ip" -Direction Inbound -RemoteAddress $ip -Action Block
            Add-Content -Path $bannedIPsPath -Value "$(Get-Date -Format \"yyyy-MM-dd HH:mm:ss\") - Banned $ip for $($failedAttempts[$ip]) failed attempts"
            Write-EventLog -LogName Application -Source "TradeBot" -EventId 1001 -EntryType Warning -Message "Banned IP $ip for $($failedAttempts[$ip]) failed login attempts"
        }
    }
}

# Clean up old bans
$cutoffTime = (Get-Date).AddMinutes(-$BanTimeMinutes)
Get-NetFirewallRule -DisplayName "Ban-*" | ForEach-Object {
    if ($_.CreationTime -lt $cutoffTime) {
        Remove-NetFirewallRule -DisplayName $_.DisplayName
        Add-Content -Path $bannedIPsPath -Value "$(Get-Date -Format \"yyyy-MM-dd HH:mm:ss\") - Unbanned $(($_.DisplayName -split \"-\")[1])"
    }
}
'@
    
    Set-Content -Path "C:\TradeBot\Scripts\fail2ban.ps1" -Value $fail2banScript
    
    # Create scheduled task to run fail2ban script
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\TradeBot\Scripts\fail2ban.ps1"
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName "TradeBot-Fail2Ban" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -Force
    
    Write-Log "Fail2Ban equivalent configured" "SUCCESS"
}

function Configure-AutoUpdates {
    Write-Log "Configuring automatic Windows updates..."
    
    # Install PSWindowsUpdate module if not already installed
    if (!(Get-Module -ListAvailable -Name PSWindowsUpdate)) {
        Install-Module PSWindowsUpdate -Force
    }
    
    # Configure automatic updates
    $autoUpdateScript = @'
# TradeBot Sentinel - Auto Update Script
Import-Module PSWindowsUpdate

# Install critical and security updates
Get-WindowsUpdate -AcceptAll -Install -AutoReboot -Criteria "IsInstalled=0 and Type='Software' and (BrowseOnly=0 or BrowseOnly=1)" -Confirm:$false

# Log update activity
Add-Content -Path "C:\TradeBot\Logs\updates.log" -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Auto update check completed"
'@
    
    Set-Content -Path "C:\TradeBot\Scripts\auto-update.ps1" -Value $autoUpdateScript
    
    # Create scheduled task for auto updates
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\TradeBot\Scripts\auto-update.ps1"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "02:00"
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName "TradeBot-AutoUpdate" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -Force
    
    Write-Log "Automatic updates configured" "SUCCESS"
}

function Configure-Auditing {
    Write-Log "Configuring Windows auditing..."
    
    # Enable audit policies
    $auditPolicies = @(
        "Audit Account Logon Events",
        "Audit Account Management",
        "Audit Directory Service Access",
        "Audit Logon Events",
        "Audit Object Access",
        "Audit Policy Change",
        "Audit Privilege Use",
        "Audit Process Tracking",
        "Audit System Events"
    )
    
    foreach ($policy in $auditPolicies) {
        try {
            auditpol /set /category:"$policy" /success:enable /failure:enable
        } catch {
            Write-Log "Failed to set audit policy: $policy" "WARNING"
        }
    }
    
    # Configure event log sizes
    wevtutil sl Security /ms:1073741824  # 1GB
    wevtutil sl System /ms:268435456     # 256MB
    wevtutil sl Application /ms:268435456 # 256MB
    
    Write-Log "Windows auditing configured" "SUCCESS"
}

function Install-AntiVirus {
    Write-Log "Configuring Windows Defender..."
    
    # Enable Windows Defender
    Set-MpPreference -DisableRealtimeMonitoring $false
    Set-MpPreference -DisableBehaviorMonitoring $false
    Set-MpPreference -DisableBlockAtFirstSeen $false
    Set-MpPreference -DisableIOAVProtection $false
    Set-MpPreference -DisablePrivacyMode $false
    Set-MpPreference -DisableScriptScanning $false
    Set-MpPreference -DisableArchiveScanning $false
    Set-MpPreference -DisableIntrusionPreventionSystem $false
    Set-MpPreference -DisableEmailScanning $false
    Set-MpPreference -DisableRemovableDriveScanning $false
    
    # Configure scan schedules
    Set-MpPreference -ScanScheduleDay Everyday
    Set-MpPreference -ScanScheduleTime 02:00:00
    
    # Update signatures
    Update-MpSignature
    
    # Add exclusions for TradeBot directories (performance)
    Add-MpPreference -ExclusionPath "C:\TradeBot\Data"
    Add-MpPreference -ExclusionPath "C:\TradeBot\Logs"
    
    Write-Log "Windows Defender configured" "SUCCESS"
}

function Create-SecurityMonitor {
    Write-Log "Creating security monitoring script..."
    
    $monitorScript = @'
# TradeBot Sentinel - Security Monitor
param([string]$AlertEmail = "admin@tradebot-sentinel.com")

$logPath = "C:\TradeBot\Logs\security-monitor.log"

function Write-SecurityLog {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Add-Content -Path $logPath -Value $logMessage
    
    if ($Level -eq "CRITICAL") {
        # Send email alert (configure SMTP settings)
        # Send-MailMessage -To $AlertEmail -Subject "CRITICAL Security Alert" -Body $Message -SmtpServer "smtp.gmail.com"
        Write-EventLog -LogName Application -Source "TradeBot" -EventId 2001 -EntryType Error -Message $Message
    }
}

# Check for failed login attempts
$failedLogins = Get-WinEvent -FilterHashtable @{LogName="Security"; ID=4625; StartTime=(Get-Date).AddHours(-1)} -ErrorAction SilentlyContinue
if ($failedLogins.Count -gt 10) {
    Write-SecurityLog "High number of failed login attempts: $($failedLogins.Count)" "WARNING"
}

# Check disk usage
$disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DriveType=3" | Where-Object {$_.DeviceID -eq "C:"}
$usage = [math]::Round((($disk.Size - $disk.FreeSpace) / $disk.Size) * 100, 2)
if ($usage -gt 90) {
    Write-SecurityLog "Disk usage critical: $usage%" "CRITICAL"
} elseif ($usage -gt 80) {
    Write-SecurityLog "Disk usage high: $usage%" "WARNING"
}

# Check memory usage
$memory = Get-WmiObject -Class Win32_OperatingSystem
$memUsage = [math]::Round((($memory.TotalVisibleMemorySize - $memory.FreePhysicalMemory) / $memory.TotalVisibleMemorySize) * 100, 2)
if ($memUsage -gt 90) {
    Write-SecurityLog "Memory usage critical: $memUsage%" "CRITICAL"
} elseif ($memUsage -gt 80) {
    Write-SecurityLog "Memory usage high: $memUsage%" "WARNING"
}

# Check TradeBot service status
$tradeBotService = Get-Service -Name "TradeBot*" -ErrorAction SilentlyContinue
if ($tradeBotService -and $tradeBotService.Status -ne "Running") {
    Write-SecurityLog "TradeBot service is not running" "CRITICAL"
}

# Check for suspicious processes
$suspiciousProcesses = Get-Process | Where-Object {$_.ProcessName -match "(nc|netcat|nmap|tcpdump|wireshark)"}
if ($suspiciousProcesses) {
    Write-SecurityLog "Suspicious processes detected: $($suspiciousProcesses.ProcessName -join ", ")" "WARNING"
}

# Check network connections
$externalConnections = Get-NetTCPConnection | Where-Object {$_.State -eq "Established" -and $_.RemoteAddress -notmatch "^(127\.|10\.|172\.|192\.168\.)"}
if ($externalConnections.Count -gt 50) {
    Write-SecurityLog "High number of external connections: $($externalConnections.Count)" "WARNING"
}

Write-SecurityLog "Security monitor completed" "INFO"
'@
    
    New-Item -ItemType Directory -Path "C:\TradeBot\Scripts" -Force | Out-Null
    Set-Content -Path "C:\TradeBot\Scripts\security-monitor.ps1" -Value $monitorScript
    
    # Create scheduled task for security monitoring
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File C:\TradeBot\Scripts\security-monitor.ps1"
    $trigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Days 365) -At (Get-Date)
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName "TradeBot-SecurityMonitor" -Action $action -Trigger $trigger -Settings $settings -User "SYSTEM" -Force
    
    Write-Log "Security monitoring configured" "SUCCESS"
}

function Create-SecurityManagement {
    Write-Log "Creating security management script..."
    
    $managementScript = @'
# TradeBot Sentinel - Security Management
param(
    [string]$Action,
    [string]$IPAddress,
    [string]$ClientName
)

function Show-SecurityStatus {
    Write-Host "=== TradeBot Sentinel Security Status ===" -ForegroundColor Cyan
    Write-Host
    
    # Firewall status
    Write-Host "Firewall Status:" -ForegroundColor Yellow
    Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction | Format-Table
    
    # Recent security events
    Write-Host "Recent Security Events:" -ForegroundColor Yellow
    Get-Content "C:\TradeBot\Logs\security-monitor.log" -Tail 10 -ErrorAction SilentlyContinue
    
    # Services status
    Write-Host "Security Services:" -ForegroundColor Yellow
    Get-Service -Name "sshd", "TradeBot*" -ErrorAction SilentlyContinue | Format-Table
    
    # Banned IPs
    Write-Host "Banned IPs:" -ForegroundColor Yellow
    Get-NetFirewallRule -DisplayName "Ban-*" -ErrorAction SilentlyContinue | Select-Object DisplayName, Enabled | Format-Table
}

function Add-AllowedIP {
    param([string]$IP)
    
    if (-not $IP) {
        Write-Error "IP address is required"
        return
    }
    
    # Validate IP format
    if ($IP -notmatch "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$") {
        Write-Error "Invalid IP address format: $IP"
        return
    }
    
    # Add firewall rule
    New-NetFirewallRule -DisplayName "Allow-$IP" -Direction Inbound -RemoteAddress $IP -Action Allow
    
    # Add to allowed IPs file
    Add-Content -Path "C:\TradeBot\Config\allowed_ips.txt" -Value $IP
    
    Write-Host "Added allowed IP: $IP" -ForegroundColor Green
}

function Remove-AllowedIP {
    param([string]$IP)
    
    if (-not $IP) {
        Write-Error "IP address is required"
        return
    }
    
    # Remove firewall rule
    Remove-NetFirewallRule -DisplayName "Allow-$IP" -ErrorAction SilentlyContinue
    
    # Remove from allowed IPs file
    $content = Get-Content "C:\TradeBot\Config\allowed_ips.txt" -ErrorAction SilentlyContinue
    $content | Where-Object {$_ -ne $IP} | Set-Content "C:\TradeBot\Config\allowed_ips.txt"
    
    Write-Host "Removed allowed IP: $IP" -ForegroundColor Green
}

function Show-Help {
    Write-Host "TradeBot Sentinel Security Management" -ForegroundColor Cyan
    Write-Host
    Write-Host "Usage: .\security-management.ps1 -Action <action> [options]" -ForegroundColor White
    Write-Host
    Write-Host "Actions:" -ForegroundColor Yellow
    Write-Host "  status                    Show security status"
    Write-Host "  allow-ip -IPAddress <ip>  Add allowed IP address"
    Write-Host "  deny-ip -IPAddress <ip>   Remove allowed IP address"
    Write-Host "  help                      Show this help message"
    Write-Host
}

switch ($Action) {
    "status" { Show-SecurityStatus }
    "allow-ip" { Add-AllowedIP -IP $IPAddress }
    "deny-ip" { Remove-AllowedIP -IP $IPAddress }
    "help" { Show-Help }
    default {
        Write-Error "Unknown action: $Action"
        Show-Help
    }
}
'@
    
    Set-Content -Path "C:\TradeBot\Scripts\security-management.ps1" -Value $managementScript
    
    Write-Log "Security management script created" "SUCCESS"
}

function Add-AllowedIP {
    param([string]$IP)
    
    if (-not $IP) {
        Write-Log "IP address is required" "ERROR"
        return
    }
    
    # Validate IP format
    if ($IP -notmatch "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$") {
        Write-Log "Invalid IP address format: $IP" "ERROR"
        return
    }
    
    # Add firewall rule
    New-NetFirewallRule -DisplayName "TradeBot-Allow-$IP" -Direction Inbound -RemoteAddress $IP -Action Allow
    
    # Add to allowed IPs file
    Add-Content -Path $Config.AllowedIPsFile -Value $IP
    
    Write-Log "Added allowed IP: $IP" "SUCCESS"
}

function Remove-AllowedIP {
    param([string]$IP)
    
    if (-not $IP) {
        Write-Log "IP address is required" "ERROR"
        return
    }
    
    # Remove firewall rule
    Remove-NetFirewallRule -DisplayName "TradeBot-Allow-$IP" -ErrorAction SilentlyContinue
    
    # Remove from allowed IPs file
    if (Test-Path $Config.AllowedIPsFile) {
        $content = Get-Content $Config.AllowedIPsFile
        $content | Where-Object {$_ -ne $IP} | Set-Content $Config.AllowedIPsFile
    }
    
    Write-Log "Removed allowed IP: $IP" "SUCCESS"
}

function Show-SecurityStatus {
    Write-Host "=== TradeBot Sentinel Security Status ===" -ForegroundColor Cyan
    Write-Host
    
    # Firewall status
    Write-Host "Firewall Status:" -ForegroundColor Yellow
    Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction | Format-Table
    
    # TradeBot firewall rules
    Write-Host "TradeBot Firewall Rules:" -ForegroundColor Yellow
    Get-NetFirewallRule -DisplayName "TradeBot*" | Select-Object DisplayName, Enabled, Direction, Action | Format-Table
    
    # Services status
    Write-Host "Security Services:" -ForegroundColor Yellow
    $services = @("sshd", "WinDefend", "EventLog")
    foreach ($service in $services) {
        $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
        if ($svc) {
            Write-Host "  $($svc.Name): $($svc.Status)" -ForegroundColor $(if ($svc.Status -eq "Running") {"Green"} else {"Red"})
        }
    }
    
    # Recent security events
    Write-Host "Recent Security Events:" -ForegroundColor Yellow
    if (Test-Path $Config.LogPath) {
        Get-Content $Config.LogPath -Tail 5
    } else {
        Write-Host "  No security log found"
    }
}

function Install-SecurityHardening {
    Write-Log "Starting TradeBot Sentinel security hardening..." "SUCCESS"
    
    if (-not (Test-Administrator)) {
        Write-Log "This script must be run as Administrator" "ERROR"
        exit 1
    }
    
    try {
        # Create event log source
        if (-not (Get-EventLog -LogName Application -Source "TradeBot" -ErrorAction SilentlyContinue)) {
            New-EventLog -LogName Application -Source "TradeBot"
        }
        
        Install-RequiredModules
        Enable-WindowsFeatures
        Install-OpenSSH
        Configure-WindowsFirewall
        Install-FailToBan
        Configure-AutoUpdates
        Configure-Auditing
        Install-AntiVirus
        Create-SecurityMonitor
        Create-SecurityManagement
        
        Write-Log "Security hardening completed successfully!" "SUCCESS"
        Write-Log "SSH port changed to: $($Config.SSHPort)" "SUCCESS"
        Write-Log "Security management: C:\TradeBot\Scripts\security-management.ps1" "SUCCESS"
        
        Write-Log "IMPORTANT: Make sure to:" "WARNING"
        Write-Log "1. Test SSH access on port $($Config.SSHPort) before closing this session" "WARNING"
        Write-Log "2. Configure your email settings for security alerts" "WARNING"
        Write-Log "3. Review and customize firewall rules as needed" "WARNING"
        Write-Log "4. Reboot the system to complete the configuration" "WARNING"
        
    } catch {
        Write-Log "Security hardening failed: $($_.Exception.Message)" "ERROR"
        throw
    }
}

# Main execution
switch ($Action.ToLower()) {
    "install" {
        Install-SecurityHardening
    }
    "status" {
        Show-SecurityStatus
    }
    "allow-ip" {
        if ($AllowedIP) {
            Add-AllowedIP -IP $AllowedIP
        } else {
            Write-Log "IP address is required for allow-ip action" "ERROR"
        }
    }
    "deny-ip" {
        if ($AllowedIP) {
            Remove-AllowedIP -IP $AllowedIP
        } else {
            Write-Log "IP address is required for deny-ip action" "ERROR"
        }
    }
    "help" {
        Write-Host "TradeBot Sentinel Security Hardening Script" -ForegroundColor Cyan
        Write-Host
        Write-Host "Usage: .\security-hardening.ps1 -Action <action> [options]" -ForegroundColor White
        Write-Host
        Write-Host "Actions:" -ForegroundColor Yellow
        Write-Host "  install                           Install and configure security hardening"
        Write-Host "  status                           Show security status"
        Write-Host "  allow-ip -AllowedIP <ip>         Add allowed IP address"
        Write-Host "  deny-ip -AllowedIP <ip>          Remove allowed IP address"
        Write-Host "  help                             Show this help message"
        Write-Host
        Write-Host "Options:" -ForegroundColor Yellow
        Write-Host "  -SSHPort <port>                  SSH port (default: 2222)"
        Write-Host "  -AllowedIP <ip>                  IP address for allow/deny actions"
        Write-Host
    }
    default {
        Write-Log "Unknown action: $Action. Use -Action help for usage information." "ERROR"
    }
}