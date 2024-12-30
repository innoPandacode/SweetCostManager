@echo on
SET LOG_FILE=setup_log.txt

:: Ensure the script is running in the same directory as the .bat file
cd /d %~dp0
echo Current directory: %cd% >> %LOG_FILE%

:: Check Python installation
python --version >> %LOG_FILE% 2>&1
IF %errorlevel% NEQ 0 (
    echo Python not found. Please check your Python installation. >> %LOG_FILE%
    echo Installation aborted. >> %LOG_FILE%
    pause
    exit /b
)

:: Check if requirements.txt exists
IF NOT EXIST requirements.txt (
    echo requirements.txt not found. >> %LOG_FILE%
    echo Installation aborted. Please ensure the requirements.txt file exists in the current directory.
    pause
    exit /b
)
echo requirements.txt found. >> %LOG_FILE%

:: Upgrade pip
python -m pip install --upgrade pip >> %LOG_FILE% 2>&1
IF %errorlevel% NEQ 0 (
    echo Failed to upgrade pip. Check permissions or network connection. >> %LOG_FILE%
    echo Installation aborted. >> %LOG_FILE%
    pause
    exit /b
)

:: Install dependencies from requirements.txt
python -m pip install -r requirements.txt >> %LOG_FILE% 2>&1
IF %errorlevel% NEQ 0 (
    echo Dependency installation failed. Check %LOG_FILE% for details. >> %LOG_FILE%
    echo Installation aborted. >> %LOG_FILE%
    pause
    exit /b
)

:: Completion message
echo Installation completed successfully. >> %LOG_FILE%
echo Installation completed successfully! Check %LOG_FILE% for details.
pause
