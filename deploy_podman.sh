#!/usr/bin/env bash
set -e

APP_NAME="packing-list"
IMAGE_NAME="packing-list-a-app:latest"
HOST_PORT="8002"
CONTAINER_PORT="8002"

echo "=== Deploying $APP_NAME with Podman on Port $HOST_PORT ==="

# 1. Stop and remove existing container if running
if podman ps -a --format '{{.Names}}' | grep -Eq "^${APP_NAME}\$"; then
    echo "Stopping and removing existing container: $APP_NAME..."
    podman stop -t 10 "$APP_NAME" || true
    podman rm -f "$APP_NAME" || true
fi

# 2. Build the Podman image
echo "Building image $IMAGE_NAME..."
podman build -t "$IMAGE_NAME" .

# 3. Run the container
echo "Running container on port $HOST_PORT (container port $CONTAINER_PORT)..."
podman run -d \
    --name "$APP_NAME" \
    --restart unless-stopped \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -e STREAMLIT_SERVER_PORT=8002 \
    -e STREAMLIT_SERVER_HEADLESS=true \
    -e STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    "$IMAGE_NAME"

# 4. Display status
echo "Container started successfully!"
podman ps --filter "name=$APP_NAME"
echo ""
echo "App is accessible at: http://<server-ip>:$HOST_PORT"
