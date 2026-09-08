@echo off
chcp 65001 >nul
title تسجيل الدخول إلى Firebase
echo ========================================================
echo   تسجيل الدخول إلى حساب Firebase للنشر على milm.web.app
echo ========================================================
set "PATH=%~dp0.tools\node;%PATH%"
call "%~dp0.tools\node\firebase.cmd" login
echo.
pause
