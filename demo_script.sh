#!/bin/bash
echo "Starting 2-minute AutoCTF demo..."
sleep 2
docker compose -f vulnerable-app/docker-compose.yml up -d
python -u agent/main.py