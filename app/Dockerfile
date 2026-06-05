FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py verify_vpn.py ./

# Verify VPN then start the app
CMD ["sh", "-c", "python verify_vpn.py && python main.py"]
