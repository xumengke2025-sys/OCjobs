@echo off
chcp 65001 >nul
echo ==========================================
echo       正在启动 万年 (Wannian)...
echo ==========================================

echo.
echo [1/2] 启动后端服务 (Backend)...
start "Wannian Backend" cmd /k "cd backend && call venv\Scripts\activate && python run.py"

echo.
echo [2/2] 启动前端服务 (Frontend)...
start "Wannian Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================
echo       服务启动中...
echo ==========================================
echo 后端地址: http://localhost:5002
echo 前端地址: http://localhost:5173
echo.
echo 请等待浏览器窗口弹出或手动访问前端地址。
echo.
pause
