@echo off
title Olympic Medals ML Project
cd /d "%~dp0"
echo.
echo ===== Olympic Medals: first ML project =====
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found.
  echo 1. Install Python 3 from https://www.python.org/downloads/
  echo 2. On the first install screen, TICK "Add python.exe to PATH".
  echo 3. Then double-click this file again.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [1/3] Creating a private Python environment in .venv ...
  python -m venv .venv
  if errorlevel 1 ( echo Could not create the environment. & pause & exit /b 1 )
)

echo [2/3] Installing libraries (first time takes a few minutes) ...
".venv\Scripts\python.exe" -m pip install --upgrade pip -q
".venv\Scripts\python.exe" -m pip install -r requirements.txt -q
if errorlevel 1 ( echo Installing libraries failed. Check your internet connection. & pause & exit /b 1 )

echo [3/3] Opening Jupyter in your browser ...
echo Keep this black window open while you work. Close it when you're done.
".venv\Scripts\python.exe" -m notebook
pause
