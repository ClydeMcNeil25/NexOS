@echo off
setlocal

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [SYSTEM]: EZRA SILENT RUN START

python run_core.py
if errorlevel 1 exit /b 1

python run_visual.py
if errorlevel 1 exit /b 1

python render_visual.py
if errorlevel 1 exit /b 1

python run_caption.py
if errorlevel 1 exit /b 1

echo [SYSTEM]: EZRA SILENT RUN COMPLETE
exit /b 0
