@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Cai thu vien Python cho Win AIO ===
python -m pip install --upgrade pywebview requests
echo.
echo Xong! Chay tool bang ChayTool.bat
pause
