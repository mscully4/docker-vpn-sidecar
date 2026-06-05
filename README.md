# docker-vpn-sidecar

Docker Compose template for routing a specific container's traffic through **ProtonVPN** (WireGuard) using the **gluetun VPN sidecar pattern**. The host machine's traffic is unaffected — only the `app` container goes through the tunnel.

## How it works

```
                   ┌──────────────────────────┐
                   │     docker-compose        │
                   │                          │
  Internet ───────►│  ┌──────┐    ┌─────────┐ │
                   │  │ gluetun│◄───│  app    │ │
                   │  │ (vpn)  │    │(Python) │ │
                   │  └───▲────┘    └─────────┘ │
                   │      │                     │
                   │  WireGuard                  │
                   │  Tunnel                     │
                   └──────┼─────────────────────┘
                          │
                   ┌──────▼────┐
                   │ ProtonVPN  │
                   │  Server    │
                   └────────────┘
```

- `gluetun` establishes and maintains a WireGuard tunnel to ProtonVPN
- The `app` container uses `network_mode: "service:vpn"` to **inherit gluetun's network namespace** — all its traffic goes through the tunnel
- If the VPN drops, the **kill switch** cuts all network access (no IP leak)
- The host machine's own traffic is completely unaffected

## Prerequisites

- **Docker** and **Docker Compose** installed on a Linux host
- A **ProtonVPN paid plan** (WireGuard requires a paid subscription)
- The `tun` kernel module loaded: `lsmod | grep tun`

## Quick start

### 1. Get your WireGuard credentials

1. Log in to [account.proton.me](https://account.proton.me)
2. Go to **VPN → Downloads → WireGuard configuration**
3. Platform: **Router**, choose your preferred country
4. Download the `.conf` file
5. Open it and copy the `PrivateKey` from the `[Interface]` section
6. Paste it into the `.env` file below

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env` and fill in your credentials:

```env
PROTONVPN_WIREGUARD_PRIVATE_KEY=your_private_key_here
PROTONVPN_SERVER_COUNTRIES=United States
```

### 3. Start

```bash
docker compose up -d
```

### 4. Verify the VPN is working

```bash
docker compose exec app python verify_vpn.py
```

The output should show a **ProtonVPN IP address**, not your real IP:

```
Outbound IP: 185.159.x.x
If this is a ProtonVPN IP, the tunnel is working correctly.
```

## File structure

```
├── docker-compose.yml   # VPN sidecar + app services
├── .env                 # gitignored — real credentials
├── .env.example         # committed — placeholder values
├── .gitignore
├── README.md
└── app/
    ├── Dockerfile       # Python 3.12 slim image
    ├── requirements.txt
    ├── main.py          # Your application entry point
    └── verify_vpn.py    # Prints the container's public IP
```

## Configuration reference

| Environment variable | Required | Description |
|---|---|---|
| `PROTONVPN_WIREGUARD_PRIVATE_KEY` | Yes | Private key from ProtonVPN WireGuard config export |
| `PROTONVPN_SERVER_COUNTRIES` | No | Country filter, e.g. `United States` (default) |

### Optional gluetun env vars

| Variable | Purpose |
|---|---|
| `FIREWALL_OUTBOUND_SUBNETS` | Allow access to LAN IPs while tunneled (e.g. `192.168.0.0/16`) |
| `DOT` | DNS-over-TLS — set to `on` (enabled by default here) |

Full gluetun docs: [ProtonVPN setup](https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/protonvpn.md)

## Exposing ports

If your app listens on a port (e.g., a web server on 8080), declare it on the **`vpn` service**, not the `app` service:

```yaml
services:
  vpn:
    ports:
      - "8080:8080"    # ← here
  app:
    # no ports section  ← not here
```

This is because the app shares the VPN container's network namespace.

## Kill switch

Gluetun's firewall blocks all outbound traffic that doesn't go through the tunnel. If the WireGuard connection drops, the app container **loses all internet access** rather than leaking traffic over the host connection. This is intentional and cannot be disabled.

## Troubleshooting

**Container won't start / health check failing:**
```bash
docker compose logs vpn
```
Look for `INFO [wireguard] WireGuard setup completed` in the logs.

**App has no network:**
The VPN tunnel may not be fully up yet. The health check in `depends_on` ensures the app waits, but if the tunnel drops later, the kill switch cuts traffic. Restart:
```bash
docker compose restart vpn
```

**Verify DNS isn't leaking:**
```bash
docker compose exec app nslookup example.com
```

## License

MIT
