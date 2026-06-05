"""Verify that outbound traffic is routed through the VPN tunnel.

Prints the public IP seen by this container. If the VPN is working correctly,
this will be a ProtonVPN exit node IP — not the host machine's real IP.
"""

import sys
import time

import requests

MAX_RETRIES = 10
RETRY_DELAY = 3  # seconds


def get_public_ip() -> str:
    """Return the public IPv4 address seen by this container."""
    resp = requests.get("https://api.ipify.org?format=json", timeout=10)
    resp.raise_for_status()
    return resp.json()["ip"]


def main() -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ip = get_public_ip()
            print(f"Outbound IP: {ip}")
            print("If this is a ProtonVPN IP, the tunnel is working correctly.")
            return
        except requests.RequestException as e:
            print(f"Attempt {attempt}/{MAX_RETRIES}: {e}", file=sys.stderr)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    print("VPN verification failed after all retries.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
