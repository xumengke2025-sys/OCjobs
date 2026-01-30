@echo off
chcp 65001 >nul
echo ==========================================
echo       正在启动 万年 (Wannian)...
echo ==========================================

:: 检查后端环境
if not exist "backend\venv\Scripts\activate.bat" (
    echo [错误] 找不到后端虚拟环境，请先运行 install_all.bat。
    pause
    exit /b
)

echo.
echo [1/2] 正在后台启动后端服务...
start "Wannian-Backend" cmd /c "cd /d %~dp0backend && call venv\Scripts\activate && python run.py"

echo.
echo [2/2] 正在后台启动前端服务...
start "Wannian-Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo ------------------------------------------
echo 启动指令已发送。
echo 如果窗口没有自动弹出，请手动访问：
echo 前端: http://localhost:5173
echo 后端: http://localhost:5002
echo ------------------------------------------
echo 按任意键关闭此窗口 (不会停止已启动的服务)。
pause >nul
