#!/bin/bash
set -e

# =============================================
# Deploy script for Social Network DRF API
# =============================================

APP_NAME="social_network_drf"
COMPOSE_FILE="docker-compose.yml"

echo "=========================================="
echo "  Deploying $APP_NAME"
echo "=========================================="

# Pull latest changes from git repository
echo "[1/5] Pulling latest code..."
git pull origin main || echo "Git pull skipped (no git remote configured yet)"

# Build and restart docker compose services
echo "[2/5] Building Docker images..."
docker compose -f $COMPOSE_FILE build --no-cache

echo "[3/5] Starting containers..."
docker compose -f $COMPOSE_FILE up -d

# Run Django migrations inside container
echo "[4/5] Running migrations..."
docker compose -f $COMPOSE_FILE exec web python manage.py migrate --noinput

# Collect Django static files
echo "[5/5] Collecting static files..."
docker compose -f $COMPOSE_FILE exec web python manage.py collectstatic --noinput --link || echo "Collectstatic skipped or not configured"

echo "=========================================="
echo "  Deployment complete!"
echo "=========================================="
docker compose -f $COMPOSE_FILE ps
