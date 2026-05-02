@echo off
chcp 65001 >nul
echo ==============================================
echo        Hexo 全自动备份 + 部署脚本
echo ==============================================
echo.

:: 1. 切换到你的源码分支 yuanma
echo [1/5] 切换到 yuanma 源码分支...
git checkout yuanma
echo.

:: 2. Git 备份源码
echo [2/5] 备份源码到 GitHub yuanma 分支...
git add .
git commit -m "自动备份源码 %date% %time%"
:: 无文件修改时跳过错误
if errorlevel 1 echo 无文件需要备份
git push origin yuanma
echo.

:: 3. 清理缓存
echo [3/5] 执行 hexo clean...
hexo clean
echo.

:: 4. 生成网站
echo [4/5] 执行 hexo generate...
hexo g
echo.

:: 5. 部署网站到 main 分支
echo [5/5] 执行 hexo deploy...
hexo d
echo.

echo ==============================================
echo              全部执行完成！🎉
echo        源码已备份 | 网站已部署上线
echo ==============================================
pause