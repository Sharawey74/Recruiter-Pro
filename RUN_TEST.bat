@echo off
REM Quick test runner for Stage 1
REM Run this from anywhere in the HR-Project directory

echo.
echo ============================================================
echo  STAGE 1 - Quick Verification
echo ============================================================
echo.

cd /d "%~dp0"
python run_verification.py

echo.
pause
