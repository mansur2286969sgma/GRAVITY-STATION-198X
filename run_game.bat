@echo off
title Gravity Station: 198X
cd /d "%~dp0"
echo Starting Gravity Station: 198X...
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] An error occurred while launching the game.
    pause
)
