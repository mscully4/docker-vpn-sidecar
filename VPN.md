# Handoff: Docker Container VPN Split Tunneling with ProtonVPN + Gluetun

## Objective

Set up a Docker Compose configuration where a specific Python application container routes all its traffic through ProtonVPN, while the rest of the host machine's traffic is unaffected. This uses a **VPN sidecar pattern** with `gluetun`.

---

## Background & Key Decisions

- The host machine is an **Ubuntu server** running Docker Compose
- VPN provider is **ProtonVPN** (WireGuard protocol)
- The goal is **per-container** VPN isolation — not host-level routing
- `gluetun` is the chosen VPN sidecar image (`qmcgaw/gluetun`) — it handles the WireGuard tunnel and exposes a kill switch by default
- The Python app container uses `network_mode: "service:vpn"` to inherit the gluetun container's network namespace entirely

---

## What to Build

### 1. `docker-compose.yml`

Create a Docker Compose file with two services:

**`vpn` service (gluetun):**
- Image: `qmcgaw/gluetun`
- Requires `NET_ADMIN` capability and `/dev/net/tun` device
- Configured for ProtonVPN WireGuard via environment variables
- Credentials loaded from a `.env` file (not hardcoded)
- Any ports the Python app needs to expose should be declared here (since the app shares this container's network namespace)

**`app` service (Python application):**
- `network_mode: "service:vpn"` — this is the critical line
- `depends_on: vpn` with a health check condition so the app only starts once the VPN tunnel is confirmed up
- No `ports` section (ports must be on the `vpn` service instead)

### 2. `.env` file (with `.env.example`)

The following variables should be externalized to a `.env` file:

```
PROTONVPN_WIREGUARD_PRIVATE_KEY=   # From ProtonVPN WireGuard config export
PROTONVPN_SERVER_COUNTRIES=        # e.g. "United States"
```

Provide a `.env.example` with placeholder values and instructions. The `.env` file itself should be in `.gitignore`.

### 3. Health check on the VPN container

Gluetun supports a built-in HTTP control server on port 8000. Use it for the health check:

```
GET http://localhost:8000/v1/vpn/status
```

Returns `{"status":"running"}` when the tunnel is up. Wire this into the `vpn` service's `healthcheck` and use `condition: service_healthy` in the `app` service's `depends_on`.

### 4. Verification script (`verify_vpn.py`)

A simple Python script the app can run at startup (or on demand) to confirm it's actually going through the VPN:

```python
import requests
response = requests.get("https://api.ipify.org?format=json")
print(f"Outbound IP: {response.json()['ip']}")
```

This should print the VPN server's IP, not the host's real IP. Include this as a sanity check.

---

## Credentials Setup Instructions (for README)

The agent should include clear steps in a `README.md` for how to get the WireGuard credentials from ProtonVPN:

1. Log in to [account.proton.me](https://account.proton.me)
2. Navigate to **VPN → Downloads → WireGuard configuration**
3. Select platform: **Router**, choose the desired server/country
4. Download the `.conf` file
5. Open it and copy the `PrivateKey` value from the `[Interface]` section
6. Paste into `.env` as `PROTONVPN_WIREGUARD_PRIVATE_KEY`

---

## File Structure

```
project/
├── docker-compose.yml
├── .env                  # gitignored, real credentials
├── .env.example          # committed, placeholder values
├── .gitignore
├── README.md
└── app/
    ├── Dockerfile
    ├── main.py           # Python entry point
    └── verify_vpn.py     # IP verification utility
```

---

## Gluetun Environment Variable Reference

For ProtonVPN WireGuard, the required gluetun env vars are:

| Variable | Value |
|---|---|
| `VPN_SERVICE_PROVIDER` | `protonvpn` |
| `VPN_TYPE` | `wireguard` |
| `WIREGUARD_PRIVATE_KEY` | From `.env` |
| `SERVER_COUNTRIES` | From `.env` (e.g. `United States`) |

Optional but useful:
- `FIREWALL_OUTBOUND_SUBNETS` — if the app needs to reach LAN resources (e.g. local Docker networks) while tunneled
- `DOT=on` — enables DNS-over-TLS inside the container for leak prevention

Full gluetun ProtonVPN docs: https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/protonvpn.md

---

## Important Behaviors to Be Aware Of

- **Kill switch is on by default** — if the VPN tunnel drops, the app container loses all network access rather than falling back to the host IP. This is intentional.
- **Ports must be declared on the `vpn` service**, not the `app` service, since they share a network namespace.
- **The app container has no independent network interface** — it sees only what gluetun exposes via the tunnel.
- **DNS is handled by gluetun** — no DNS leak risk as long as the app uses gluetun's resolver (default behavior when sharing the network namespace).

---

## Out of Scope

- The contents of `app/main.py` — the actual Python application logic is not part of this task
- ProtonVPN account setup or plan upgrades (WireGuard requires a paid plan)
- Multi-server failover or load balancing across VPN endpoints
