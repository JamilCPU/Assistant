#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Sets up WireGuard VPN for the AI Assistant platform.
    Creates server and client configs so remote devices can access the assistant.

.DESCRIPTION
    Interactive setup that:
    1. Verifies WireGuard is installed
    2. Generates keypairs for the server and each client device
    3. Writes wg0.conf (server) and per-client .conf files
    4. Optionally installs WireGuard as a Windows service
    5. Generates QR codes for mobile clients (if qrencode is available)

.NOTES
    WireGuard download: https://www.wireguard.com/install/
    Run as Administrator from the project root: .\scripts\setup-wireguard.ps1
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Config ────────────────────────────────────────────────────────────────────
$VPN_SUBNET    = "10.0.0.0/24"
$SERVER_IP     = "10.0.0.1"
$SERVER_PORT   = 51820
$DNS           = "1.1.1.1"
$CONFIG_DIR    = "C:\ProgramData\WireGuard"
$OUTPUT_DIR    = Join-Path $PSScriptRoot "wireguard-configs"
$TUNNEL_NAME   = "wg0"

# ── Helpers ───────────────────────────────────────────────────────────────────

function Write-Header($text) {
    Write-Host "`n$("─" * 60)" -ForegroundColor Cyan
    Write-Host "  $text" -ForegroundColor Cyan
    Write-Host "$("─" * 60)" -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host "  → $text" -ForegroundColor Green
}

function Write-Warn($text) {
    Write-Host "  ⚠ $text" -ForegroundColor Yellow
}

function Find-WireGuard {
    # Look for wg.exe in common install locations
    $candidates = @(
        "C:\Program Files\WireGuard\wg.exe",
        "C:\Program Files (x86)\WireGuard\wg.exe",
        (Get-Command wg -ErrorAction SilentlyContinue)?.Source
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) { return $c }
    }
    return $null
}

function Generate-KeyPair($wg) {
    $private = & $wg genkey
    $public  = $private | & $wg pubkey
    return @{ Private = $private; Public = $public }
}

function Get-PublicIP {
    try {
        return (Invoke-RestMethod "https://api.ipify.org?format=text" -TimeoutSec 5).Trim()
    } catch {
        return $null
    }
}

# ── Main ──────────────────────────────────────────────────────────────────────

Write-Header "AI Assistant — WireGuard VPN Setup"

# 1. Check WireGuard
Write-Step "Looking for WireGuard..."
$wg = Find-WireGuard
if (-not $wg) {
    Write-Host "`n  WireGuard is not installed." -ForegroundColor Red
    Write-Host "  Download it from: https://www.wireguard.com/install/" -ForegroundColor White
    Write-Host "  Install, then re-run this script.`n" -ForegroundColor White
    exit 1
}
Write-Step "Found: $wg"

# Ensure wireguard.exe (the UI) is also available for service installation
$wireguardExe = Join-Path (Split-Path $wg) "wireguard.exe"

# 2. Output directory
New-Item -ItemType Directory -Path $OUTPUT_DIR -Force | Out-Null
Write-Step "Config output dir: $OUTPUT_DIR"

# 3. Public IP detection
Write-Header "Network Configuration"
$publicIP = Get-PublicIP
if ($publicIP) {
    Write-Host "  Detected public IP: $publicIP" -ForegroundColor White
    $endpoint = Read-Host "  WireGuard endpoint (press Enter to use $publicIP, or type a DDNS hostname)"
    if ([string]::IsNullOrWhiteSpace($endpoint)) { $endpoint = $publicIP }
} else {
    Write-Warn "Could not auto-detect public IP."
    $endpoint = Read-Host "  Enter your public IP or DDNS hostname (e.g. yourname.duckdns.org)"
}
$endpointFull = "${endpoint}:${SERVER_PORT}"
Write-Step "Endpoint: $endpointFull"

# 4. Client count
$clientCount = 0
do {
    $input = Read-Host "`n  How many client devices do you want to add? (1-20)"
    $clientCount = [int]::TryParse($input, [ref]$clientCount) ? $clientCount : 0
} while ($clientCount -lt 1 -or $clientCount -gt 20)

# 5. Client names
$clients = @()
for ($i = 1; $i -le $clientCount; $i++) {
    $name = Read-Host "  Name for client $i (e.g. phone, laptop, tablet)"
    if ([string]::IsNullOrWhiteSpace($name)) { $name = "client$i" }
    $clients += $name -replace '[^a-zA-Z0-9_-]', '_'
}

# 6. Generate keypairs
Write-Header "Generating Keypairs"

Write-Step "Server keypair..."
$serverKeys = Generate-KeyPair $wg

$clientKeys = @{}
foreach ($name in $clients) {
    Write-Step "Client '$name' keypair..."
    $clientKeys[$name] = Generate-KeyPair $wg
}

# 7. Write server config
Write-Header "Writing Server Config"

$peerBlocks = ""
$octet = 2
foreach ($name in $clients) {
    $clientIP = "10.0.0.$octet"
    $peerBlocks += @"

# Client: $name
[Peer]
PublicKey = $($clientKeys[$name].Public)
AllowedIPs = ${clientIP}/32

"@
    $octet++
}

$serverConf = @"
[Interface]
PrivateKey = $($serverKeys.Private)
Address = ${SERVER_IP}/24
ListenPort = $SERVER_PORT
DNS = $DNS
$peerBlocks
"@

$serverConfPath = Join-Path $OUTPUT_DIR "wg0.conf"
$serverConf | Out-File -FilePath $serverConfPath -Encoding ascii
Write-Step "Server config: $serverConfPath"

# Also write to WireGuard config dir for service installation
$wgConfigPath = Join-Path $CONFIG_DIR "wg0.conf"
New-Item -ItemType Directory -Path $CONFIG_DIR -Force | Out-Null
$serverConf | Out-File -FilePath $wgConfigPath -Encoding ascii
Write-Step "Installed to: $wgConfigPath"

# 8. Write client configs
Write-Header "Writing Client Configs"

$octet = 2
foreach ($name in $clients) {
    $clientIP = "10.0.0.$octet"
    $clientConf = @"
[Interface]
PrivateKey = $($clientKeys[$name].Private)
Address = ${clientIP}/24
DNS = $DNS

[Peer]
PublicKey = $($serverKeys.Public)
Endpoint = $endpointFull
# Route only the VPN subnet through the tunnel (split tunnel)
AllowedIPs = ${VPN_SUBNET}
PersistentKeepalive = 25
"@
    $clientPath = Join-Path $OUTPUT_DIR "${name}.conf"
    $clientConf | Out-File -FilePath $clientPath -Encoding ascii
    Write-Step "Client '$name': $clientPath  (VPN IP: $clientIP)"
    $octet++
}

# 9. QR codes (optional)
Write-Header "QR Codes for Mobile Clients"
$qrTool = Get-Command qrencode -ErrorAction SilentlyContinue
if ($qrTool) {
    foreach ($name in $clients) {
        $clientPath = Join-Path $OUTPUT_DIR "${name}.conf"
        $qrPath     = Join-Path $OUTPUT_DIR "${name}.png"
        Write-Step "Generating QR for '$name'..."
        & qrencode -t PNG -o $qrPath -r $clientPath
        Write-Host "    Saved: $qrPath" -ForegroundColor Gray
    }
} else {
    Write-Warn "qrencode not found — skipping QR code generation."
    Write-Host "  To generate QR codes later:" -ForegroundColor Gray
    Write-Host "    1. Open WireGuard GUI → Add tunnel → Import from file → select a .conf" -ForegroundColor Gray
    Write-Host "    2. The GUI shows a QR code you can scan with the WireGuard mobile app" -ForegroundColor Gray
}

# 10. Install WireGuard service
Write-Header "Install WireGuard as Windows Service"
$installService = Read-Host "  Install wg0 as a Windows service (auto-starts on boot)? [Y/n]"
if ($installService -ne 'n' -and $installService -ne 'N') {
    if (Test-Path $wireguardExe) {
        Write-Step "Installing tunnel service..."
        & $wireguardExe /installtunnelservice $wgConfigPath
        Write-Step "Service installed. Starting tunnel..."
        Start-Service -Name "WireGuardTunnel`$$TUNNEL_NAME" -ErrorAction SilentlyContinue
        Write-Step "WireGuard tunnel is running."
    } else {
        Write-Warn "wireguard.exe not found at $wireguardExe — install via WireGuard GUI instead."
        Write-Host "    Open WireGuard GUI → Add tunnel → $wgConfigPath" -ForegroundColor Gray
    }
}

# 11. Router port-forward reminder
Write-Header "Router Configuration Required"
Write-Host @"
  You MUST forward the following port on your router:

    Protocol : UDP
    External : $SERVER_PORT
    Internal : $SERVER_PORT → (this computer's local IP)

  Steps:
    1. Find your local IP: run  ipconfig  and look for IPv4 Address
    2. Log into your router (usually http://192.0.2.1 or http://192.0.2.1)
    3. Find Port Forwarding / NAT and add the rule above

  Optional — Dynamic DNS (if your public IP changes):
    • DuckDNS (free): https://www.duckdns.org — run their update script on startup
    • No-IP (free tier): https://www.noip.com

"@ -ForegroundColor White

# 12. Build + serve reminder
Write-Header "Make the Assistant Accessible Over VPN"
Write-Host @"
  After connecting a client to the VPN, they access the assistant at:

    http://${SERVER_IP}:8000/ui     ← built frontend (after running npm run build)
    http://${SERVER_IP}:8000        ← API only

  To build the frontend once and serve it from the backend:
    cd frontend-web
    npm run build
    cd ..
    .venv\Scripts\python.exe -m backend.gateway.main

  The /ui path is automatically served by FastAPI when frontend-web/dist exists.

"@ -ForegroundColor White

Write-Header "Setup Complete"
Write-Host "  Server config : $serverConfPath" -ForegroundColor Green
Write-Host "  Client configs: $OUTPUT_DIR\*.conf" -ForegroundColor Green
Write-Host ""
Write-Host "  Send each client's .conf file to the device and import it in the WireGuard app." -ForegroundColor White
Write-Host "  iOS/Android: scan the QR code or import the file." -ForegroundColor White
Write-Host ""
