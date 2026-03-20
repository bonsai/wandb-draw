@echo off
REM Doraemon 2D Render - Git Workflow
REM Run locally to generate and commit image

setlocal

REM Get current commit hash
for /f "delims=" %%i in ('git rev-parse --short HEAD') do set COMMIT_HASH=%%i

echo ========================================
echo Doraemon 2D Render
echo Commit: %COMMIT_HASH%
echo ========================================

REM Run Blender
"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe" --background --python run_doraemon.py

if %ERRORLEVEL% neq 0 (
    echo Error: Blender script failed
    exit /b %ERRORLEVEL%
)

REM Commit generated image
set PNG_FILE=doraemon_2d_%COMMIT_HASH%.png

if exist %PNG_FILE% (
    git add %PNG_FILE%
    git commit -m "chore: auto-generate doraemon image [skip ci]"
    echo Committed %PNG_FILE%
) else (
    echo Error: PNG file not found
)

endlocal