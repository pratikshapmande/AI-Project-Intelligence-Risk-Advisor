@echo off
setlocal
cd /d "%~dp0backend"
if not exist .venv (
  echo Creating Python 3.12 virtual environment...
  py -3.12 -m venv .venv
  if errorlevel 1 (
    echo ERROR: Python 3.12 was not found. Install Python 3.12 and try again.
    pause
    exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip --version >nul 2>&1 || (echo ERROR: pip is unavailable.& pause & exit /b 1)
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Backend dependencies could not be installed. Check internet access and the messages above.
  pause
  exit /b 1
)
echo.
echo Starting FastAPI at http://127.0.0.1:8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
