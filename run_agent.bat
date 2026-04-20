@echo off
setlocal

cls

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [SYSTEM]: INITIALIZING EZRA NEX
echo [DIRECTORY]: %CD%
echo --------------------------------------------

if not exist ".env" (
    echo [ERROR]: .env not found!
    pause
    exit /b 1
)

if not exist "agent_state.md" (
    echo [ERROR]: agent_state.md not found!
    pause
    exit /b 1
)

if not exist "EN_MEM.txt" (
    echo [ERROR]: EN_MEM.txt not found!
    pause
    exit /b 1
)

if not exist "core_system_prompt.txt" (
    echo [ERROR]: core_system_prompt.txt not found!
    pause
    exit /b 1
)

if not exist "visual_system_prompt.txt" (
    echo [ERROR]: visual_system_prompt.txt not found!
    pause
    exit /b 1
)

if not exist "caption_system_prompt.txt" (
    echo [ERROR]: caption_system_prompt.txt not found!
    pause
    exit /b 1
)

if not exist "daily_creative_override.json" (
    echo [ERROR]: daily_creative_override.json not found!
    pause
    exit /b 1
)

if not exist "daily_visual_state.json" (
    echo [ERROR]: daily_visual_state.json not found!
    pause
    exit /b 1
)

if not exist "run_history.json" (
    echo [ERROR]: run_history.json not found!
    pause
    exit /b 1
)

if not exist "run_core.py" (
    echo [ERROR]: run_core.py not found!
    pause
    exit /b 1
)

if not exist "run_visual.py" (
    echo [ERROR]: run_visual.py not found!
    pause
    exit /b 1
)

if not exist "render_visual.py" (
    echo [ERROR]: render_visual.py not found!
    pause
    exit /b 1
)

if not exist "run_caption.py" (
    echo [ERROR]: run_caption.py not found!
    pause
    exit /b 1
)

echo [PHASE 1]: Running Core Agent...
python run_core.py
if errorlevel 1 (
    echo [ERROR]: Core Agent failed.
    pause
    exit /b 1
)

echo [PHASE 2]: Running Visual Agent...
python run_visual.py
if errorlevel 1 (
    echo [ERROR]: Visual Agent failed.
    pause
    exit /b 1
)

echo [PHASE 3]: Rendering Visual...
python render_visual.py
if errorlevel 1 (
    echo [ERROR]: Visual renderer failed.
    pause
    exit /b 1
)

echo [PHASE 4]: Running Caption Agent...
python run_caption.py
if errorlevel 1 (
    echo [ERROR]: Caption Agent failed.
    pause
    exit /b 1
)

echo --------------------------------------------
echo [SYSTEM]: EZRA CYCLE COMPLETE.
pause
exit /b 0
