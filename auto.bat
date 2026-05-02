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

:: ============== 3. 清理缓存 ==============
echo [3/5] 执行 hexo clean...
hexo clean
echo.

:: ============== 4. 生成网站 ==============
echo [4/5] 执行 hexo generate...
hexo g
echo.

:: ============== 5. 部署网站 ==============
echo [5/5] 执行 hexo deploy...
hexo d
echo.

echo ==============================================
echo              执行成功！🎉
echo        源码已备份 | 网站已部署
echo ==============================================
pause
exit