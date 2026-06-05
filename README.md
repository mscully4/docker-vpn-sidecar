# docker-vpn-sidecar

A reusable **gluetun VPN sidecar** for Docker Compose — routes traffic through **ProtonVPN** (WireGuard) with a kill switch. Other projects use `network_mode: "service:vpn"` to inherit the tunnel without configuring their own VPN.

## How it works

```
                 ┌──────────────────────────────┐
                 │  docker compose (this repo)   │
                 │                              │
Internet ───────►│  ┌──────────┐                │
                 │  │ gluetun  │                │
                 │  │  (vpn)   │                │
                 │  └───▲──────┘                │
                 │      │ WireGuard              │
                 └──────┼───────────────────────┘
                        │
                 ┌──────▼────┐      ┌─────────────┐
                 │ ProtonVPN  │      │ other-proj/ │
                 │  Server    │      │ docker-compose.yml
                 └────────────┘      │              │
                                     │ services:    │
                                     │   myapp:     │
                                     │     network_mode: │
                                     │       "service:vpn" │
                                     └─────────────┘
```

- This repo runs **just gluetun** — no app container
- Other projects join its network and use `network_mode: "service:vpn"` to route through the tunnel
- If the VPN drops, the kill switch cuts all traffic (no IP leak)
- The host machine's own traffic is completely unaffected

## Prerequisites

- **Docker** and **Docker Compose** on a Linux host
- A **ProtonVPN paid plan** (WireGuard requires a paid subscription)
- The `tun` kernel module loaded: `lsmod | grep tun`

## Setup

### 1. Get your WireGuard credentials

1. Log in to [account.proton.me](https://account.proton.me)
2. Go to **VPN → Downloads → WireGuard configuration**
3. Platform: **Router**, choose your preferred country
4. Download the `.conf` file
5. Open it and copy the `PrivateKey` from the `[Interface]` section
6. Paste it into `.env`

### 2. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
PROTONVPN_WIREGUARD_PRIVATE_KEY=your_private_key_here
PROTONVPN_SERVER_COUNTRIES=Ireland
```

### 3. Start

```bash
docker compose up -d
```

### 4. Verify

```bash
docker compose exec vpn wget -qO- http://localhost:8000/v1/vpn/status
# → {"status":"running"}
```

## Using it from another project

### Option A: Shared Compose network (recommended)

In your other project's `docker-compose.yml`:

```yaml
services:
  myapp:
    image: your-app
    network_mode: "service:vpn"
    depends_on:
      vpn:
        condition: service_healthy
```

Then start both together from the sidecar directory:

```bash
docker compose -f docker-vpn-sidecar/docker-compose.yml -f myproject/docker-compose.yml up -d
```

Or more conveniently, drop a `compose.yml` in your project root that includes both:

```yaml
# myproject/compose.yml
include:
  - ../docker-vpn-sidecar/docker-compose.yml

services:
  myapp:
    image: your-app
    network_mode: "service:vpn"
    depends_on:
      vpn:
        condition: service_healthy
```

### Option B: Extend the sidecar directly

```yaml
# myproject/docker-compose.yml
services:
  vpn:
    extends:
      file: ../docker-vpn-sidecar/docker-compose.yml
      service: vpn

  myapp:
    image: your-app
    network_mode: "service:vpn"
    depends_on:
      vpn:
        condition: service_healthy
```

## Exposing ports

Ports go on the **`vpn` service**, not your app, since they share a network namespace:

```yaml
services:
  vpn:
    ports:
      - "8080:8080"    # ← here
  myapp:
    # no ports          ← not here
    network_mode: "service:vpn"
```

## File structure

```
├── docker-compose.yml   # gluetun VPN sidecar
├── .env                 # gitignored — real credentials
├── .env.example         # committed — placeholder values
├── .gitignore
├── README.md
└── VPN.md               # original design spec
```

## Configuration reference

| Variable | Required | Description |
|---|---|---|
| `PROTONVPN_WIREGUARD_PRIVATE_KEY` | Yes | Private key from ProtonVPN WireGuard config |
| `PROTONVPN_SERVER_COUNTRIES` | No | Country filter, e.g. `Ireland` |

### Optional gluetun env vars

| Variable | Purpose |
|---|---|
| `FIREWALL_OUTBOUND_SUBNETS` | Allow LAN access while tunneled (e.g. `192.168.0.0/16`) |
| `DOT` | DNS-over-TLS — `on` by default |

Full docs: [gluetun ProtonVPN setup](https://github.com/qdm12/gluetun-wiki/blob/main/setup/providers/protonvpn.md)

## Kill switch

Gluetun's firewall blocks all outbound traffic not going through the tunnel. If WireGuard drops, any container using `network_mode: "service:vpn"` **loses all internet** rather than leaking traffic.

## Troubleshooting

**Container won't start / health check failing:**
```bash
docker compose logs vpn
```
Look for `INFO [wireguard] WireGuard setup completed`.

**Check tunnel status:**
```bash
docker compose exec vpn wget -qO- http://localhost:8000/v1/vpn/status
```

## License

MIT
