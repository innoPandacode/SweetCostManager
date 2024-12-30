@echo off
echo === Starting the application, please wait... ===

:: Ensure the script runs in the directory containing the batch file
cd /d %~dp0

:: Check if the virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

:: Activate the virtual environment
call venv\Scripts\activate

:: Start Streamlit
streamlit run main.py

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start Streamlit.
    pause
    exit /b 1
)

pause
