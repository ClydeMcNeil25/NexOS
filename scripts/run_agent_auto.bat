@echo off
setlocal

cls

for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"
cd /d "%PROJECT_DIR%"

echo [AUTO]: INITIALIZING EZRA NEX AUTOMATION
echo [DIRECTORY]: %CD%
echo --------------------------------------------

if not exist "run_agent_auto.py" (
    echo [ERROR]: run_agent_auto.py not found!
    pause
    exit /b 1
)

if not exist "scripts\\run_agent.bat" (
    echo [ERROR]: scripts\\run_agent.bat not found!
    pause
    exit /b 1
)

python run_agent_auto.py
if errorlevel 1 (
    echo --------------------------------------------
    echo [AUTO]: Automation wrapper exited with an error.
    pause
    exit /b 1
)

echo --------------------------------------------
echo [AUTO]: Automation wrapper finished.
pause
exit /b 0
