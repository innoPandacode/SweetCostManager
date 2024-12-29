@echo off
echo === Setting up the environment, please wait... ===

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not detected. Please install Python first.
    pause
    exit /b 1
)

:: Create a virtual environment
if not exist venv (
    echo === Creating a virtual environment... ===
    python -m venv venv
)

:: Activate the virtual environment and install dependencies
echo === Activating the virtual environment and installing dependencies... ===
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% EQU 0 (
    echo === Setup completed successfully! ===
) else (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

pause
