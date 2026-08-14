@echo off
title Bank Application
echo.
echo  Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo  Installing required packages...
pip install flask mysql-connector-python python-dateutil --quiet

echo.
echo  Starting Bank Application...
echo.
python "%~dp0app.py"
pause
