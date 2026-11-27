@echo off
setlocal
cd /d "%~dp0frontend"
if not exist node_modules (
  echo Installing frontend dependencies for the first run...
  npm install
  if errorlevel 1 (echo ERROR: npm install failed.& pause & exit /b 1)
)
echo.
echo Starting frontend at http://127.0.0.1:5173
npm run dev
pause
