@echo off
:: 解决Windows中文乱码 + 强制脚本不中断
chcp 65001 >nul
setlocal enabledelayedexpansion
cls

echo ==============================================
echo        Hexo 全自动备份 + 部署脚本
echo ==============================================
echo.

:: ============== 1. 切换源码分支 ==============
echo [1/5] 切换到 yuanma 源码分支...
git checkout yuanma
echo.

:: ============== 2. 备份源码（无文件也不报错） ==============
echo [2/5] 备份源码中...
git add . >nul 2>&1
git commit -m "自动备份 %date% %time%" >nul 2>&1
git push origin yuanma >nul 2>&1
echo 源码备份完成！
echo.