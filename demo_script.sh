#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              AutoCTF Demo - E2B Cloud Edition              ║"
echo "║        No Docker Required - Runs on macOS 12+              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "This demo runs pentests in E2B cloud sandboxes."
echo "No local Docker installation needed!"
echo ""
echo "Starting in 2 seconds..."
sleep 2

# Run the agent (now uses E2B exclusively)
python3 -u agent/main.py
