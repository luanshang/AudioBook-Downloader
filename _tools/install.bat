@echo off
rem ============================================
rem  懒人听书畅听大师 安装脚本
rem  IExpress 自解压解压后自动执行
rem ============================================
setlocal enabledelayedexpansion

set "APP_DIR=%LOCALAPPDATA%\Programs\懒人听书畅听大师"

echo.
echo  ============================================
echo   懒人听书畅听大师 v2.0.0 安装
echo  ============================================
echo.
echo  安装目录: %APP_DIR%
echo.

rem 创建目标目录并复制全部文件（含子目录）
if not exist "%APP_DIR%" mkdir "%APP_DIR%"
xcopy "%~dp0." "%APP_DIR%\" /E /Y /Q /I >nul

rem 创建桌面快捷方式
powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\懒人听书畅听大师.lnk'); $sc.TargetPath = '%APP_DIR%\懒人畅听大师.exe'; $sc.WorkingDirectory = '%APP_DIR%'; $sc.IconLocation = '%APP_DIR%\懒人畅听大师.exe,0'; $sc.Save()"

echo.
echo  安装完成！桌面已创建快捷方式。
echo.
echo  启动: 懒人听书畅听大师
echo.
timeout /t 3 >nul
exit /b 0