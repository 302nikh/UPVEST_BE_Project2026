@echo off
echo ================================================
echo UPVEST Backend Server Startup
echo ================================================
echo.
echo Starting FastAPI backend server...
echo Server will be available at: http://localhost:5000
echo API Documentation: http://localhost:5000/docs
echo.
echo Press Ctrl+C to stop the server
echo ================================================
echo.

REM Always run from this script's directory (robust across renames/moves)
cd /d "%~dp0"
python backend_api.py

pause
