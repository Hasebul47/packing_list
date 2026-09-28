# PO to Packing List Converter

Streamlit application for extracting VF/Vans PO PDFs and converting them to formatted packing list Excel spreadsheets and PDFs.

## Deployment with Podman (Linux)

### Option 1: Quick Deployment Script
Run the automated script:
```bash
chmod +x deploy_podman.sh
./deploy_podman.sh
```

---

### Option 2: Step-by-Step Podman CLI

#### 1. Build the image
```bash
podman build -t packing-list-app:latest .
```

#### 2. Run the container on port 8002
```bash
podman run -d \
  --name packing-list \
  --restart unless-stopped \
  -p 8002:8002 \
  -e STREAMLIT_SERVER_PORT=8002 \
  -e STREAMLIT_SERVER_HEADLESS=true \
  -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
  packing-list-app:latest
```

#### 3. Verify container status and logs
```bash
# Check container status
podman ps -a --filter name=packing-list

# View real-time logs
podman logs -f packing-list
```

---

### Option 3: Using Podman Compose

If `podman-compose` is installed:
```bash
# Build and run
podman-compose up -d --build

# Check status
podman-compose ps

# Stop service
podman-compose down
```

---

### Option 4: Run as a Linux Systemd Service (Auto-start on boot)

Podman can automatically manage containers as systemd services (root or rootless):

```bash
# 1. Generate systemd service file
podman generate systemd --new --name packing-list --files

# 2. For rootless user (recommended):
mkdir -p ~/.config/systemd/user/
mv container-packing-list.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now container-packing-list.service

# To keep user services running without active SSH sessions:
loginctl enable-linger $USER
```

---

## Access the Application

Open your browser and navigate to:
```
http://<your-server-ip>:8002
```
