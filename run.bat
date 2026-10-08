@echo off
setlocal

if not exist ".\venv\Scripts\python.exe" (
    echo Virtual environment not found. Running first-time setup...
    echo.

    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment. Ensure Python is installed and in your PATH.
        pause
        exit /b 1
    )

    echo Installing dependencies. This may take some time...
    echo.
    .\venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies.
        pause
        exit /b 1
    )

    echo Setup complete.
    echo.
)

start "" .\venv\Scripts\pythonw.exe main.py
exit
