@echo off
REM Builds dist\MathFighter.exe  (run this on a Windows PC with Python 3 installed)
cd /d "%~dp0"
py -m pip install -r requirements.txt pyinstaller
py -m PyInstaller --noconfirm --onefile --windowed --name MathFighter main.py
echo Done: dist\MathFighter.exe
pause
