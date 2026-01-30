@echo off
chcp 65001 >nul
echo ==========================================
echo       万年 (Wannian) - 一键安装脚本
echo ==========================================

echo.
echo [1/4] 正在检查环境...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.10+。
    pause
    exit /b
)
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Node.js，请先安装 Node.js。
    pause
    exit /b
)

echo.
echo [2/4] 正在配置后端 (Backend)...
cd backend
if not exist venv (
    echo 正在创建虚拟环境...
    python -m venv venv
) else (
    echo 虚拟环境已存在，跳过创建。
)

echo 正在激活虚拟环境并安装依赖...
call venv\Scripts\activate
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 后端依赖安装失败。
    pause
    exit /b
)
cd ..

echo.
echo [3/4] 正在配置前端 (Frontend)...
cd frontend
echo 正在安装前端依赖 (npm install)...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 前端依赖安装失败。
    pause
    exit /b
)
cd ..

echo.
echo [4/4] 检查配置文件...
if not exist .env (
    echo 正在从 .env.example 创建 .env 文件...
    copy .env.example .env
    echo.
    echo [重要提示] 请打开根目录下的 .env 文件，填入您的 LLM_API_KEY！
) else (
    echo .env 配置文件已存在。
)

echo.
echo ==========================================
echo          安装完成！(Installation Complete)
echo ==========================================
echo.
echo 请确保 .env 文件中已配置正确的 API Key。
echo 之后您可以直接运行 start_app.bat 来启动项目。
echo.
pause
