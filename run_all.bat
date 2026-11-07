@echo off
echo ========================================================
echo  Launching Medantrik Assist Full Stack Application
echo  Single-port deployment: UI & Backend at http://127.0.0.1:8000
echo ========================================================
start "Medantrik Assist Full-Stack Server" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn api.app:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul
start http://127.0.0.1:8000
echo Medantrik Assist is now running at http://127.0.0.1:8000
