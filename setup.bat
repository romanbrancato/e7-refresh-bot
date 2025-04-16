@echo off
REM Exit on first error
setlocal

echo Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo Error: Failed to create virtual environment. Ensure Python is installed and in your PATH.
    pause
    exit /b 1
)

echo Installing dependencies...
echo This may take some time, the window will close when done.
echo.
timeout /t 3 /nobreak > nul

.\venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies.
    pause
    exit /b 1
)