@echo off
setlocal

REM Get the directory of this script
set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%venv"

REM Check if venv exists
if not exist "%VENV_DIR%" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

echo [INFO] Starting Multimodal AI Assistant...
echo [INFO] Using Virtual Environment: %VENV_DIR%

REM Activate venv and run app
call "%VENV_DIR%\Scripts\activate.bat"
python "%SCRIPT_DIR%app\main.py"

if %errorlevel% neq 0 (
    echo [ERROR] Application crashed.
    pause
)
