@echo off
REM Windows Double-Click Launcher for CSV Charset Analyzer
REM This file opens the web-based GUI in your browser
REM
REM SECURITY NOTICE: Windows may show security warnings for this file
REM because it's an executable script from the internet. This is normal.
REM If Windows Defender blocks it: Click "More info" → "Run anyway"
REM UAC prompt may appear - click "Yes" to allow
REM
REM DISCLAIMER: No warranty provided - use at your own risk
REM Always backup your data before running conversions

title CSV Charset Analyzer
color 0A

echo.
echo 🔍 CSV Charset Analyzer
echo =======================
echo.
echo ⚠️  DISCLAIMER: This software is provided AS IS without warranty.
echo    No liability accepted for any damage or data loss.
echo    Always backup your data before conversions!
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

echo 📁 Script location: %SCRIPT_DIR%

REM Check if Python files exist
if not exist "%SCRIPT_DIR%charset_web_gui.py" (
    echo ❌ Error: charset_web_gui.py not found!
    echo Please make sure all files are in the same folder:
    echo   - charset_web_gui.py
    echo   - check_csv_charset.py
    echo   - run_charset_analyzer.bat ^(this file^)
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT_DIR%check_csv_charset.py" (
    echo ❌ Error: check_csv_charset.py not found!
    echo Please make sure all files are in the same folder.
    echo.
    pause
    exit /b 1
)

REM Check if chardet is installed
echo 🔧 Checking dependencies...
python -c "import chardet" 2>nul
if errorlevel 1 (
    echo 📦 Installing chardet dependency...
    pip install chardet
    if errorlevel 1 (
        echo ❌ Failed to install chardet. Please install manually:
        echo    pip install chardet
        echo.
        pause
        exit /b 1
    )
)

echo ✅ Dependencies OK
echo.
echo 🚀 Starting CSV Charset Analyzer...
echo 🌐 Your browser will open automatically
echo.
echo 💡 Instructions:
echo    1. Browser window will open with the interface
echo    2. Enter your CSV folder path in the interface
echo    3. Choose analysis options
echo    4. Click 'Start Analysis'
echo.
echo ⏹️  To stop: Close this window or press Ctrl+C
echo.

REM Change to script directory and run
cd /d "%SCRIPT_DIR%"
python charset_web_gui.py

pause