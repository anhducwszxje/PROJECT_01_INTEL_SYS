@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3.11 -m venv .venv
    if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -c "import streamlit,torch,sklearn,pandas" >nul 2>&1
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 goto error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -m streamlit run app.py --server.address 127.0.0.1 --server.port 8521
exit /b %errorlevel%
:error
echo Setup failed. Install Python 3.11 with the Python launcher, then read docs\HUONG_DAN_CHAY.md.
pause
exit /b 1
