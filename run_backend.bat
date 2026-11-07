@echo off
echo ========================================================
echo  Starting Medantrik Assist Backend (FastAPI + WebSocket)
echo ========================================================
call .venv\Scripts\activate.bat
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
pause
