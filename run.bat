@echo off
echo Starting script...

REM Check if virtual environment directory exists
if not exist ".\venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first to create the necessary environment.
    echo.
    pause
    exit /b 1
)

REM If we get here, the environment exists, so run the script
.\venv\Scripts\python main.py

pause