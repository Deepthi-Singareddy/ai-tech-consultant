#!/usr/bin/env bash
set -e

echo "======================================================================"
echo " STARTING AI TECH CONSULTANT ENTERPRISE SUITE (ALL SERVICES)"
echo "======================================================================"

echo "[1/4] Starting Task 1: Knowledge Brain (port 8000)..."
(cd task1-knowledge-brain && python3 run.py) &
PID_TASK1=$!

sleep 3

echo "[2/4] Starting Task 2: Inbox Agent (port 3000)..."
(cd task2-inbox-agent && npm start) &
PID_TASK2=$!

sleep 3

echo "[3/4] Starting Task 3: Meeting to Scope (port 8001)..."
(cd task3-meeting-to-scope && python3 run.py) &
PID_TASK3=$!

sleep 2

echo "[4/4] Starting Unified Command Cockpit (port 5000)..."
(cd web-studio && python3 server.py) &
PID_STUDIO=$!

echo "======================================================================"
echo " ALL SERVICES RUNNING!"
echo " Unified Studio URL: http://127.0.0.1:5000"
echo " Press Ctrl+C to shut down all background services."
echo "======================================================================"

trap "kill $PID_TASK1 $PID_TASK2 $PID_TASK3 $PID_STUDIO" SIGINT SIGTERM
wait
