@echo off
set "PATH=%~dp0.tools\node;%PATH%"
"%~dp0.tools\node\firebase.cmd" deploy --only hosting
pause
