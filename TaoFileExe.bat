@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Dong goi Win AIO by Duy Anh
echo ==========================================================
echo   DONG GOI WIN AIO BY DUY ANH THANH FILE EXE (PORTABLE)
echo ==========================================================
echo.
echo [1/3] Cai thu vien can thiet...
python -m pip install --upgrade pywebview requests pyinstaller
if errorlevel 1 goto :loi
echo.
echo [2/3] Dong goi file exe (mat 1-3 phut)...
python -m PyInstaller --noconfirm --clean --onefile --noconsole --uac-admin --name "Win AIO by Duy Anh" --icon icon.ico --add-data "icon.ico;." --add-data "web;web" --collect-all webview --collect-all pythonnet --collect-all clr_loader win_aio.py
if errorlevel 1 goto :loi
copy /y "dist\Win AIO by Duy Anh.exe" "Win AIO by Duy Anh.exe" >nul
echo.
echo [3/3] XONG!
echo   Da tao "Win AIO by Duy Anh.exe" (1 file duy nhat) trong thu muc nay.
echo   Chep file exe sang USB la dung duoc.
echo.
pause
exit /b 0
:loi
echo.
echo   CO LOI! Kiem tra da cai Python (python.org, tick "Add Python to PATH") chua.
pause
exit /b 1
