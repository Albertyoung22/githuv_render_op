@echo off
chcp 65001 >nul
title GitHub & Render Desktop App 控制中心
echo ========================================================
echo   正在啟動 GitHub & Render 桌面應用程式...
echo   後端核心: Flask + Waitress WSGI (0.0.0.0:10000)
echo   語音引擎: Microsoft Edge-TTS
echo ========================================================
python desktop_app.py
pause

