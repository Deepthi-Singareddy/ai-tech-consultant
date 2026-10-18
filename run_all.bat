@echo off
echo ======================================================================
echo  STARTING AI TECH CONSULTANT ENTERPRISE SUITE (ALL SERVICES)
echo ======================================================================

echo [1/4] Starting Task 1: Knowledge Brain (Python FastAPI on port 8000)...
start "Task 1 - Knowledge Brain :8000" cmd /k "cd task1-knowledge-brain && python run.py"

timeout /t 3 /nobreak >nul

echo [2/4] Starting Task 2: Inbox Agent (TypeScript Node on port 3000)...
start "Task 2 - Inbox Agent :3000" cmd /k "cd task2-inbox-agent && npm start"

timeout /t 3 /nobreak >nul

echo [3/4] Starting Task 3: Meeting to Scope (Python FastAPI on port 8001)...
start "Task 3 - Meeting to Scope :8001" cmd /k "cd task3-meeting-to-scope && python run.py"

timeout /t 2 /nobreak >nul

echo [4/4] Starting Unified Command Cockpit (Web Studio on port 5000)...
start "Unified Studio :5000" cmd /k "cd web-studio && python server.py"

timeout /t 2 /nobreak >nul

echo ======================================================================
echo  ALL 4 SERVICES LAUNCHED SUCCESSFULLY!
echo  Unified Studio URL:   http://127.0.0.1:5000
echo  Task 1 API Docs:      http://127.0.0.1:8000/docs
echo  Task 2 API Health:    http://127.0.0.1:3000/api/v1/health
echo  Task 3 API Docs:      http://127.0.0.1:8001/docs
echo ======================================================================
start http://127.0.0.1:5000
pause
