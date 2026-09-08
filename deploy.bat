@echo off
chcp 65001 >nul
title نشر التحديثات على milm.web.app
echo ========================================================
echo   جاري نشر المنظومة وتحديث موقع milm.web.app ...
echo ========================================================
set PATH=%~dp0.tools\node;%PATH%
call npx -y firebase-tools@latest deploy --only hosting
echo.
echo ========================================================
echo   اكتمل النشر بنجاح! يمكنك فتح https://milm.web.app
echo ========================================================
pause
