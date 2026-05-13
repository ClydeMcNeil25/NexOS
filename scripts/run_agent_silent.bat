@echo off
setlocal

for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"
cd /d "%PROJECT_DIR%"

echo [SYSTEM]: INITIALIZING EZRA NEX
echo [DIRECTORY]: %CD%
echo --------------------------------------------

if not exist ".env" (
    echo [ERROR]: .env not found!
    exit /b 1
)

if not exist "data\\agent_state.md" (
    echo [ERROR]: data\\agent_state.md not found!
    exit /b 1
)

if not exist "data\\EN_MEM.txt" (
    echo [ERROR]: data\\EN_MEM.txt not found!
    exit /b 1
)

if not exist "core_system_prompt.txt" (
    echo [ERROR]: core_system_prompt.txt not found!
    exit /b 1
)

if not exist "visual_system_prompt.txt" (
    echo [ERROR]: visual_system_prompt.txt not found!
    exit /b 1
)

if not exist "caption_system_prompt.txt" (
    echo [ERROR]: caption_system_prompt.txt not found!
    exit /b 1
)

if not exist "data\\daily_creative_override.json" (
    echo [ERROR]: data\\daily_creative_override.json not found!
    exit /b 1
)

if not exist "data\\daily_visual_state.json" (
    echo [ERROR]: data\\daily_visual_state.json not found!
    exit /b 1
)

if not exist "data\\run_history.json" (
    echo [ERROR]: data\\run_history.json not found!
    exit /b 1
)

if not exist "run_core.py" (
    echo [ERROR]: run_core.py not found!
    exit /b 1
)

if not exist "run_visual.py" (
    echo [ERROR]: run_visual.py not found!
    exit /b 1
)

if not exist "render_visual.py" (
    echo [ERROR]: render_visual.py not found!
    exit /b 1
)

if not exist "run_caption.py" (
    echo [ERROR]: run_caption.py not found!
    exit /b 1
)

if not exist "post_to_webhook.py" (
    echo [ERROR]: post_to_webhook.py not found!
    exit /b 1
)

echo [PHASE 1]: Running Core Agent...
python run_core.py
if errorlevel 1 (
    echo [ERROR]: Core Agent failed.
    exit /b 1
)

echo [PHASE 2]: Running Visual Agent...
python run_visual.py
if errorlevel 1 (
    echo [ERROR]: Visual Agent failed.
    exit /b 1
)

echo [PHASE 3]: Rendering Visual...
python render_visual.py
if errorlevel 1 (
    echo [ERROR]: Visual renderer failed.
    exit /b 1
)

echo [PHASE 4]: Running Caption Agent...
python run_caption.py
if errorlevel 1 (
    echo [ERROR]: Caption Agent failed.
    exit /b 1
)

echo [PHASE 5]: Running Social Publishing...
python post_to_webhook.py
if errorlevel 1 (
    echo [ERROR]: Social Publishing failed.
    exit /b 1
)

echo --------------------------------------------
echo [SYSTEM]: EZRA CYCLE COMPLETE.
exit /b 0
