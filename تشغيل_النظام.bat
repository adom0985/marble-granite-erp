@echo off
chcp 65001 > nul
cd /d "C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp"
echo ========================================================
echo   نظام إدارة وفواتير وحسابات الرخام والجرانيت
echo   خالي أحمد جلال - الإصدار المتقدم 2026
echo ========================================================
echo جاري تشغيل الخادم على الرابط: http://localhost:8000
echo.
python -m uvicorn server:app --host 127.0.0.1 --port 8000
pause
