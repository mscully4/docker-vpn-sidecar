"""Verify that outbound traffic is routed through the VPN tunnel.

Prints the public IP seen by this container. If the VPN is working correctly,
this will be a ProtonVPN exit node IP — not the host machine's real IP.
"""

import requests


def get_public_ip() -> str:
    """Return the public IPv4 address seen by this container."""
    resp = requests.get("https://api.ipify.org?format=json", timeout=10)
    resp.raise_for_status()
    return resp.json()["ip"]


def main() -> None:
    ip = get_public_ip()
    print(f"Outbound IP: {ip}")
    print("If this is a ProtonVPN IP, the tunnel is working correctly.")


if __name__ == "__main__":
    main()
