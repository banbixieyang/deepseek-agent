@echo off
rem ds-agent 一键启动（Windows 双击入口）
setlocal
set "HERE=%~dp0"
for %%I in ("%HERE%..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%start.ps1" %*
set RC=%ERRORLEVEL%
endlocal & exit /b %RC%
