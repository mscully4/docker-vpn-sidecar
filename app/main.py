"""Replace this with your actual application logic.

Your code runs inside a container whose entire network stack is
routed through ProtonVPN via the gluetun sidecar. All outbound
requests from here will use the VPN exit node.
"""

import time


def main() -> None:
    print("VPN-sidecar app started.")
    print("All traffic from this container is routed through ProtonVPN.")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
