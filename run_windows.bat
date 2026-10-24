@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo          SmartHostel - Aurora Oasis
echo ==============================================

if not exist "venv\Scripts\python.exe" (
  echo Creating local Python environment...
  python -m venv venv
  if errorlevel 1 goto :error
)

echo Installing required packages...
"venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :error

set FLASK_DEBUG=1
echo.
echo Starting SmartHostel. Open http://127.0.0.1:5000 in your browser.
echo Keep this window open while presenting the demo.
"venv\Scripts\python.exe" app.py
goto :end

:error
echo.
echo Setup failed. Confirm Python 3.10+ is installed and your internet connection is available for pip.
pause
exit /b 1

:end
endlocal
