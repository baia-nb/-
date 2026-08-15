@echo off
chcp 65001 >nul
REM ============================================================
REM  我的世界格式转换器 - 打包脚本
REM  参考架构: 插件化 + 核心 + GUI
REM ============================================================
setlocal

cd /d "%~dp0"

set PYTHONDONTWRITEBYTECODE=1

echo [1/3] 清理旧构建 / cleaning old build...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo [2/3] PyInstaller 打包 / packaging...
pyinstaller mc_converter.spec --noconfirm
if errorlevel 1 (
    echo [错误] 打包失败 / PyInstaller failed
    pause
    exit /b 1
)

echo.
echo [3/3] 替换 EXE 图标 / replace icon...
if exist "change_icon.py" (
    python change_icon.py
)

echo.
echo ============================================================
echo  打包完成! 输出: dist\我的世界格式转换器.exe
echo  Build done! Output: dist\我的世界格式转换器.exe
echo ============================================================
pause
