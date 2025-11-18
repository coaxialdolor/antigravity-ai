@echo off
setlocal

echo ===================================================
echo Multimodal AI Assistant - One-Click Installer
echo ===================================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not detected! Please install Python 3.10+ and add it to your PATH.
    pause
    exit /b 1
)

echo [INFO] Python detected. Starting installation process...

REM Run the Python installer script
python installer/install.py

if %errorlevel% neq 0 (
    echo [ERROR] Installation failed. See logs above.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Installation complete!
echo You can now run the application using 'run.bat'.
echo.
pause
