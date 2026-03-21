# Plan 06 — Remote Access via WireGuard VPN

## Problem
The app only works on `localhost`. The README lists "VPN Access: Accessible via VPN mesh for remote devices" as a feature but nothing is implemented. The user wants to access the assistant from a phone, tablet, or another laptop over the internet.

---

## Approach: Self-hosted WireGuard

WireGuard creates an encrypted point-to-point mesh. The workstation acts as a "server peer" (always-on endpoint). Remote devices connect as "client peers" and get a private VPN IP. Once connected, clients reach the assistant at the workstation's VPN IP (e.g. `10.0.0.1:8000`).

This requires:
1. WireGuard installed on the workstation
2. One WireGuard config file per client device
3. A port forwarded on the router (UDP, default 51820) so remote clients can reach the workstation
4. The frontend served over HTTP (or HTTPS with a self-signed cert) on the VPN interface

---

## Step 1 — Install WireGuard

Download and install: https://www.wireguard.com/install/ (Windows installer)

This adds:
- WireGuard GUI
- `wg` and `wg-quick` CLI tools (available from PowerShell/CMD after install)

---

## Step 2 — Key Generation

For each peer (server + each client), generate a keypair:

```powershell
# In PowerShell (after WireGuard install)
wg genkey | Tee-Object -FilePath server_private.key | wg pubkey > server_public.key
wg genkey | Tee-Object -FilePath client1_private.key | wg pubkey > client1_public.key
```

Store these securely. The private keys never leave their respective devices.

---

## Step 3 — Server Config (`wg0.conf`)

Create `C:\ProgramData\WireGuard\wg0.conf`:

```ini
[Interface]
PrivateKey = <SERVER_PRIVATE_KEY>
Address = 10.0.0.1/24
ListenPort = 51820
DNS = 1.1.1.1

# Client: Phone
[Peer]
PublicKey = <CLIENT1_PUBLIC_KEY>
AllowedIPs = 10.0.0.2/32

# Client: Laptop
[Peer]
PublicKey = <CLIENT2_PUBLIC_KEY>
AllowedIPs = 10.0.0.3/32
```

Install as a Windows service so it starts automatically:
```powershell
wireguard /installtunnelservice C:\ProgramData\WireGuard\wg0.conf
```

---

## Step 4 — Client Configs

One config per device. Example for a phone:

```ini
[Interface]
PrivateKey = <CLIENT1_PRIVATE_KEY>
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = <YOUR_PUBLIC_IP_OR_DDNS>:51820
AllowedIPs = 10.0.0.0/24   # only route VPN subnet through tunnel
PersistentKeepalive = 25
```

Generate a QR code for mobile:
```powershell
# Install qrencode via Scoop or Chocolatey, then:
qrencode -t ansiutf8 < client1.conf
```

Or use the WireGuard GUI to import the config file → it shows a QR code automatically.

---

## Step 5 — Router Port Forwarding

Forward **UDP port 51820** from the router's WAN interface to the workstation's local IP.
- Log into router admin panel
- Create a port forwarding rule: `UDP 51820 → <WORKSTATION_LOCAL_IP>:51820`

If the public IP changes (most home ISPs), use a free DDNS service:
- **DuckDNS** (free): `yourname.duckdns.org` → run their Windows update script on startup
- **No-IP** (free tier): similar

---

## Step 6 — Expose the Assistant on the VPN Interface

The FastAPI backend already binds to `0.0.0.0:8000`, so it's reachable at `10.0.0.1:8000` once WireGuard is up.

The React frontend needs to be either:

**Option A — Serve the built frontend from FastAPI (recommended)**
```python
# In main.py — after building the frontend
app.mount("/", StaticFiles(directory="frontend-web/dist", html=True), name="frontend")
```
Add a `npm run build` step. Then the whole app is served from `http://10.0.0.1:8000`.

Add a build script to `package.json`:
```json
"scripts": {
  "build": "vite build",
  "preview": "vite preview --host 0.0.0.0 --port 5173"
}
```

The built frontend must point API calls to `/api` (relative URLs) which it already does.

**Option B — Run Vite dev server on VPN interface**
```
vite --host 0.0.0.0 --port 5173
```
Access at `http://10.0.0.1:5173`. Fine for development.

---

## Step 7 — CORS and API Key Security

Once exposed to VPN clients:

**CORS**: Restrict allowed origins in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://10.0.0.1:8000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**API Key**: Set an API key in `config/default_config.json` → `server.api_key`. The frontend reads this from settings and includes it in all requests via `X-API-Key` header.

**Permissions**: The config already has `permissions.remote_mode: "restricted"` which limits remote connections to read-only file tools. Ensure the middleware or auth layer sets the permission mode based on whether the request comes from VPN (`10.0.0.x`) vs localhost.

---

## Step 8 — Optional: HTTPS with Self-Signed Cert

For browsers that block features over HTTP (mic, etc.):

```powershell
# Generate self-signed cert
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=10.0.0.1"
```

Update `main.py` startup:
```python
uvicorn.run("backend.gateway.main:app", host="0.0.0.0", port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem")
```

Clients will need to accept the self-signed cert once in their browser.

---

## Summary of what to build in the app (code changes)

### `backend/gateway/main.py`
- Mount built frontend static files
- Restrict CORS to VPN + localhost origins (configurable)

### `backend/gateway/middleware.py`
- Detect if request source IP is in VPN subnet (`10.0.0.x`) vs localhost
- Attach `is_remote: bool` to request state
- Pass to guardrails for permission enforcement

### `backend/services/chat_service/tools/guardrails.py`
- Read `is_remote` from request context to apply `remote_mode` restrictions

### New script: `scripts/setup-wireguard.ps1`
- Interactive PowerShell script that:
  1. Checks WireGuard is installed
  2. Generates server keypair
  3. Prompts for number of clients, generates their keypairs and configs
  4. Writes `wg0.conf` and per-client `.conf` files
  5. Installs WireGuard tunnel service
  6. Reminds user to set up port forwarding

### `frontend-web/vite.config.ts`
- Configure `build.outDir` to `../backend/static/frontend` so FastAPI can serve it

---

## Files to touch
- `backend/gateway/main.py` — serve built frontend, restrict CORS
- `backend/gateway/middleware.py` — detect remote vs local
- `backend/services/chat_service/tools/guardrails.py` — use request context for permissions
- `frontend-web/vite.config.ts` — set build output dir
- `scripts/setup-wireguard.ps1` — new helper script

---

## Acceptance criteria
- [ ] WireGuard tunnel established on workstation (auto-starts on boot)
- [ ] Phone/laptop connects to VPN and gets `10.0.0.x` address
- [ ] Full app accessible at `http://10.0.0.1:8000` from VPN clients
- [ ] API key required for remote connections
- [ ] File tool restrictions apply to remote connections (remote_mode)
- [ ] Disconnecting VPN immediately loses access to the app
