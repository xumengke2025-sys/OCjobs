@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ==========================================
echo       万年 (Wannian) - 增强型安装脚本
echo ==========================================

:: 1. 检查 Python
set PYTHON_CMD=python
where !PYTHON_CMD! >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    set PYTHON_CMD=py
    where !PYTHON_CMD! >nul 2>nul
    if !ERRORLEVEL! NEQ 0 (
        echo [错误] 未检测到 Python (python 或 py^)。请先前往 python.org 安装。
        pause
        exit /b
    )
)
echo [确认] 使用命令: !PYTHON_CMD!

:: 2. 检查 Node.js
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未检测到 Node.js。请先安装 Node.js (建议 v16+^)。
    pause
    exit /b
)
echo [确认] 检测到 Node.js/npm

:: 3. 配置后端
echo.
echo [1/3] 正在配置后端 (Backend)...
if not exist "backend" (
    echo [错误] 找不到 backend 文件夹，请在项目根目录运行此脚本。
    pause
    exit /b
)

cd backend
if not exist venv (
    echo 正在创建虚拟环境...
    !PYTHON_CMD! -m venv venv
)

echo 正在安装后端依赖 (可能需要几分钟)...
call venv\Scripts\activate
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 后端依赖安装失败。请检查网络连接。
    pause
    exit /b
)
cd ..

:: 4. 配置前端
echo.
echo [2/3] 正在配置前端 (Frontend)...
if not exist "frontend" (
    echo [错误] 找不到 frontend 文件夹。
    pause
    exit /b
)

cd frontend
echo 正在安装前端依赖 (npm install)...
call npm install --registry=https://registry.npmmirror.com
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 前端依赖安装失败。
    pause
    exit /b
)
cd ..

:: 5. 配置文件
echo.
echo [3/3] 检查配置文件...
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo [提示] 已生成 .env 文件，请务必填入 LLM_API_KEY。
    ) else (
        echo [警告] 找不到 .env.example，请手动创建 .env 文件。
    )
)

echo.
echo ==========================================
echo          安装完成！请配置 .env 后启动
echo ==========================================
pause
