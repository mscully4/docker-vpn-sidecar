FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py verify_vpn.py ./

# Optional: run VPN verification on startup, then launch the app
# CMD ["sh", "-c", "python verify_vpn.py && python main.py"]
