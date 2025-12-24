@echo off
REM RAG Research Assistant - 快速启动脚本 (Windows)
REM MVP 1.0

echo ========================================
echo   RAG Research Assistant - MVP 1.0
echo   快速启动脚本
echo ========================================
echo.

REM 检查 .env 文件
if not exist "backend\.env" (
    echo [错误] 未找到 backend\.env 文件
    echo.
    echo 请执行以下步骤:
    echo 1. 复制 backend\.env.example 为 backend\.env
    echo 2. 在 .env 文件中填入你的 API Key
    echo    - DASHSCOPE_API_KEY (阿里云通义千问)
    echo    - 或 OPENAI_API_KEY (OpenAI)
    echo.
    pause
    exit /b 1
)

echo [1/4] 检查环境...
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python, 请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 检查 Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js, 请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [2/4] 启动后端服务...
echo.
cd backend
start "RAG Backend" cmd /k "python main.py"
cd ..

REM 等待后端启动
timeout /t 3 /nobreak >nul

echo [3/4] 启动前端服务...
echo.
start "RAG Frontend" cmd /k "npm start"

echo [4/4] 完成!
echo.
echo ========================================
echo   服务已启动:
echo   - 后端: http://localhost:8000
echo   - 前端: http://localhost:3000
echo   - API文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause >nul
