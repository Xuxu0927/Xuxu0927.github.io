#!/bin/bash
# ============================================================
# 每日热门新闻自动部署脚本
# 用法: bash deploy_news.sh
#
# 流程:
#   1. 拉取 yuanma 分支最新代码
#   2. 运行 Python 抓取脚本 (conda tech-news 环境)
#   3. 如果有新文件，commit + push 到 yuanma 分支
#   4. GitHub Actions 自动构建并部署到 main 分支
#
# 配合 Windows 任务计划程序每日执行
# ============================================================

set -e

# 切换到博客仓库目录
BLOG_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BLOG_DIR"

# 初始化 conda（兼容 Git Bash）
CONDA_BASE="$(dirname "$(dirname "$(which conda)")")"
source "$CONDA_BASE/etc/profile.d/conda.sh" 2>/dev/null || true
conda activate tech-news 2>/dev/null || true

echo "============================================"
echo "  每日热门新闻 - 自动部署"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  目录: $BLOG_DIR"
echo "  Python: $(which python)"
echo "============================================"
echo ""

# ---- 1. 确保在 yuanma 分支并拉取最新代码 ----
echo "[STEP 1/4] 拉取 yuanma 分支最新代码..."
git checkout yuanma 2>/dev/null || true
git pull --rebase origin yuanma 2>&1 || echo "  [INFO] 拉取失败（网络问题或首次），继续..."

# ---- 2. 运行 Python 抓取脚本 ----
echo ""
echo "[STEP 2/4] 抓取热门新闻..."
python fetch_tech_news.py

# ---- 3. 检查是否有新文件 ----
echo ""
echo "[STEP 3/4] 检查变更..."

NEW_POSTS=$(git status --porcelain source/_posts/ 2>/dev/null | grep "^?" | wc -l)
MODIFIED=$(git status --porcelain source/_posts/ 2>/dev/null | grep "^[MA]" | wc -l)
CHANGES=$((NEW_POSTS + MODIFIED))

if [ "$CHANGES" -eq 0 ]; then
    echo "  [INFO] 无新增新闻文件，跳过部署。"
    exit 0
fi

echo "  [INFO] 发现 ${CHANGES} 个变更文件"

# ---- 4. 提交 & 推送（触发 GitHub Actions 自动部署） ----
echo ""
echo "[STEP 4/4] 提交并推送到 yuanma 分支..."

git add source/_posts/
git add fetch_tech_news.py deploy_news.sh 2>/dev/null || true

TODAY=$(date '+%Y-%m-%d')
git commit -m "📰 每日热门新闻 - ${TODAY}" \
           -m "自动抓取并生成 ${TODAY} 的热门新闻" \
           -m "Co-Authored-By: Tech News Bot <bot@xuxu0927.github.io>"

git push origin yuanma

echo ""
echo "============================================"
echo "  推送完成！GitHub Actions 正在自动部署..."
echo "  稍后访问: https://xuxu0927.github.io/"
echo "============================================"
