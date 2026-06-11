@echo off
echo ================================
echo  AI Minecraft Builder
echo ================================
echo.

REM Check if model.pkl exists — if not, run setup first
IF NOT EXIST model.pkl (
    echo First time setup detected...
    echo Running setup — this may take a minute.
    echo.
    python setup.py
) ELSE (
    echo Starting game...
    python main.py
)

pause
