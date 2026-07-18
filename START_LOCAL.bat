@echo off
title Shared Grunge Portal Timer
cd /d "%~dp0"
set ADMIN_KEY=change-me
set DATA_DIR=%~dp0data
py app.py
if errorlevel 1 python app.py
pause
