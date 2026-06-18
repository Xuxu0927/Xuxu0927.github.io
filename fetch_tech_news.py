#!/usr/bin/env python3
"""
每日热门新闻自动抓取脚本
从多个免费数据源获取当日最火热的新闻与项目，生成 Hexo 兼容的 Markdown 文件。

数据来源:
  - Hacker News Top Stories (hacker-news.firebaseio.com) — 全球技术社区最热讨论
  - Hacker News Show HN (hacker-news.firebaseio.com) — 开发者展示精选
  - GitHub Trending (github.com/trending) — 当日最火开源仓库

输出: source/_posts/<YYYY-MM-DD>-hot-news.md
"""

import json
import urllib.request
import urllib.error
import re
import os
from datetime import datetime, timezone, timedelta

# ============================================================
# 配置
# ============================================================
BLOG_SOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source", "_posts")
MAX_HN_TOP = 15          # Hacker News 热门最多取几条
MAX_SHOW_HN = 10         # Show HN 最多取几条
MAX_GH_TRENDING = 10     # GitHub Trending 最多取几条
USER_AGENT = "Mozilla/5.0 (compatible; HotNewsBot/1.0)"
REQUEST_TIMEOUT = 15     # 秒

# 北京时间
TZ_BEIJING = timezone(timedelta(hours=8))

# ============================================================
# 工具函数
# ============================================================

def fetch_json(url):
    """请求 JSON API，返回解析后的 dict/list，失败返回 None。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [WARN] 请求失败: {url} — {e}")
        return None

def fetch_html(url):
    """请求 HTML 页面，返回文本，失败返回 None。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [WARN] 请求失败: {url} — {e}")
        return None

# ============================================================
# 新闻源 1: Hacker News 最热头条（主力来源）
# ============================================================

def fetch_hacker_news_top():
    """
    获取 Hacker News 首页最热门故事。
    按热度（score）排序，不设关键词过滤，呈现社区最关注的讨论。
    API: https://github.com/HackerNews/API
    """
    print("[INFO] 正在抓取 Hacker News 最热头条...")

    # 1. 获取 top stories ID 列表
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        print("  [FAIL] 无法获取 Hacker News 列表")
        return []

    # 2. 逐条获取详情
    articles = []
    # 获取更多条目以便有足够候选（去除非 story 类型后仍有 MAX_HN_TOP 条）
    fetch_count = min(len(ids), MAX_HN_TOP * 3)
    for item_id in ids[:fetch_count]:
        if len(articles) >= MAX_HN_TOP:
            break
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        if not item:
            continue
        # 只取有 URL 的 story 类型
        if item.get("type") != "story":
            continue
        title = item.get("title", "(无标题)")
        url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")
        score = item.get("score", 0)
        comments = item.get("descendants", 0)
        articles.append({
            "title": title,
            "url": url,
            "summary": (
                f"该文章在 Hacker News 上获得 **{score}** 点热度，"
                f"共有 **{comments}** 条评论讨论，位列今日最热头条。"
            ),
            "source": "Hacker News 最热",
        })

    print(f"  [OK] Hacker News 最热头条: {len(articles)} 篇")
    return articles

# ============================================================
# 新闻源 2: Hacker News Show HN（开发者展示项目）
# ============================================================

def fetch_show_hn():
    """获取 Hacker News Show HN 热门展示项目。"""
    print("[INFO] 正在抓取 Show HN 热门项目...")

    ids = fetch_json("https://hacker-news.firebaseio.com/v0/showstories.json")
    if not ids:
        print("  [FAIL] 无法获取 Show HN 列表")
        return []

    articles = []
    for item_id in ids[:MAX_SHOW_HN * 2]:
        if len(articles) >= MAX_SHOW_HN:
            break
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        if not item:
            continue
        title = item.get("title", "(无标题)")
        url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")
        score = item.get("score", 0)
        comments = item.get("descendants", 0)
        articles.append({
            "title": title,
            "url": url,
            "summary": (
                f"该项目由开发者在 Hacker News 的 Show HN 栏目展示，"
                f"获得 **{score}** 点热度，共有 **{comments}** 条讨论反馈。"
            ),
            "source": "Show HN",
        })

    print(f"  [OK] Show HN: {len(articles)} 篇")
    return articles

# ============================================================
# 新闻源 3: GitHub Trending
# ============================================================

# 编程语言名称中英对照
LANG_NAMES = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Java": "Java",
    "Go": "Go",
    "Rust": "Rust",
    "C++": "C++",
    "C": "C 语言",
    "C#": "C#",
    "Ruby": "Ruby",
    "Swift": "Swift",
    "Kotlin": "Kotlin",
    "PHP": "PHP",
    "HTML": "HTML",
    "CSS": "CSS",
    "Shell": "Shell 脚本",
    "Vue": "Vue",
    "Jupyter Notebook": "Jupyter Notebook",
    "Dart": "Dart",
    "Scala": "Scala",
    "Lua": "Lua",
    "R": "R 语言",
    "Zig": "Zig",
    "MDX": "MDX",
}


def format_github_summary(lang, stars, desc):
    """生成 GitHub 项目的中文摘要。"""
    parts = []
    if lang:
        lang_cn = LANG_NAMES.get(lang, lang)
        parts.append(f"编程语言：**{lang_cn}**")
    if stars:
        parts.append(f"⭐ **{stars}**")
    if desc:
        parts.append(f"简介：{desc}")
    return " | ".join(parts) if parts else "GitHub 今日热门仓库"


def fetch_github_trending():
    """
    抓取 GitHub Trending 页面（今日热门仓库）。
    解析 <article class="Box-row"> 中的仓库信息。
    """
    print("[INFO] 正在抓取 GitHub Trending...")

    html = fetch_html("https://github.com/trending")
    if not html:
        print("  [FAIL] 无法获取 GitHub Trending")
        return []

    # 按 article 分块解析
    articles_html = re.findall(
        r'<article\s+class="Box-row">(.*?)</article>',
        html,
        re.DOTALL,
    )

    articles = []
    for art_html in articles_html:
        # 1. 提取仓库路径
        repo_m = re.search(
            r'<h2\s+class="h3\s+lh-condensed">\s*<a[^>]*href="/([^"]+)"[^>]*>',
            art_html,
        )
        if not repo_m:
            continue
        full_name = repo_m.group(1).strip()

        # 2. 提取描述
        desc_m = re.search(
            r'<p\s+class="[^"]*col-9[^"]*color-fg-muted[^"]*my-1[^"]*"[^>]*>\s*(.*?)\s*</p>',
            art_html,
            re.DOTALL,
        )
        desc = desc_m.group(1).strip() if desc_m else ""
        desc = re.sub(r'<[^>]+>', '', desc).strip()

        # 3. 提取编程语言
        lang_m = re.search(
            r'<span\s+itemprop="programmingLanguage"[^>]*>\s*(.*?)\s*</span>',
            art_html,
        )
        lang = lang_m.group(1).strip() if lang_m else ""

        # 4. 提取 stars 数量
        stars_m = re.search(
            r'<a[^>]*href="/[^"]+/stargazers"[^>]*>\s*(.*?)\s*</a>',
            art_html,
            re.DOTALL,
        )
        stars = ""
        if stars_m:
            stars_text = re.sub(r'<[^>]+>', '', stars_m.group(1)).strip()
            stars = stars_text

        title = f"{full_name}"
        if desc:
            title += f" — {desc}"

        articles.append({
            "title": title,
            "url": f"https://github.com/{full_name}",
            "summary": format_github_summary(lang, stars, desc),
            "source": "GitHub Trending",
        })

        if len(articles) >= MAX_GH_TRENDING:
            break

    print(f"  [OK] GitHub Trending: {len(articles)} 篇")
    return articles

# ============================================================
# 生成 Hexo Markdown
# ============================================================

SOURCE_INTROS = {
    "🔥 Hacker News 最热头条": (
        "Hacker News 是 Y Combinator 旗下的知名技术社区，由硅谷创业教父 Paul Graham 创立。"
        "这里汇集了全球开发者当日最关注的科技话题与行业讨论——不设主题过滤，"
        "纯粹按社区热度排序，呈现技术圈真正的「今日最火」。"
    ),
    "💡 Show HN 热门项目": (
        "Show HN 是 Hacker News 上的特色栏目，供开发者展示自己打造的项目和产品。"
        "从开源工具到创意应用，每天都有令人眼前一亮的创新作品涌现。"
    ),
    "📦 GitHub Trending 热门仓库": (
        "GitHub Trending 展示了当日最受关注的开源仓库，按 star 增长速度排序。"
        "涵盖各类编程语言与领域，是发现优秀开源项目的最佳途径。"
    ),
}


def generate_hexo_post(articles_by_source, target_date):
    """
    将新闻数据生成 Hexo 兼容的 Markdown 文件。

    articles_by_source: [(source_name, [articles]), ...]
    target_date: datetime.date 对象
    """
    date_str = target_date.strftime("%Y-%m-%d")
    filename = f"{date_str}-hot-news.md"
    filepath = os.path.join(BLOG_SOURCE_DIR, filename)

    total = sum(len(articles) for _, articles in articles_by_source)

    # 构建 Markdown 内容
    lines = []
    lines.append("---")
    lines.append(f"title: 每日热门新闻 - {date_str}")
    lines.append(f"date: {date_str}")
    lines.append("tags: [热门新闻, 技术资讯, HackerNews, GitHub]")
    lines.append("categories: 热门资讯")
    lines.append("---")
    lines.append("")

    # 一级标题
    lines.append(f"# 每日热门新闻 - {date_str}")
    lines.append("")

    # 概览信息
    lines.append(f"> 📰 自动化抓取于 {datetime.now(TZ_BEIJING).strftime('%Y-%m-%d %H:%M')} (北京时间)")
    lines.append(f"> 📊 共收录 **{total}** 条热门新闻与项目")
    lines.append("")

    # 中文简介
    lines.append(
        "本文每日自动汇总全球技术圈最火热的资讯：首先为你带来 **Hacker News** 当日热度最高的头条讨论，"
        "随后是 **Show HN** 开发者展示精选，最后附上 **GitHub Trending** "
        "当日最火开源项目，帮你快速掌握技术圈今日焦点。"
    )
    lines.append("")

    lines.append("<!-- more -->")
    lines.append("")

    # 各新闻源板块
    for source_name, articles in articles_by_source:
        lines.append(f"## {source_name}")
        lines.append("")

        intro = SOURCE_INTROS.get(source_name)
        if intro:
            lines.append(f"> {intro}")
            lines.append("")

        for a in articles:
            lines.append(f"### [{a['title']}]({a['url']})")
            lines.append("")
            if a.get("summary"):
                lines.append(f"> {a['summary']}")
                lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(
        "*本文由自动化脚本每日生成，如有问题请 "
        "[提交 Issue](https://github.com/Xuxu0927/Xuxu0927.github.io/issues)。*"
    )

    content = "\n".join(lines)

    # 写入文件
    os.makedirs(BLOG_SOURCE_DIR, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n[OK] 已生成: {filepath}  ({total} 条新闻)")
    return filepath

# ============================================================
# 主流程
# ============================================================

def main():
    print("=" * 60)
    print("  每日热门新闻抓取")
    print(f"  运行时间: {datetime.now(TZ_BEIJING).strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print("=" * 60)
    print()

    today = datetime.now(TZ_BEIJING).date()

    all_news = []

    # 1. Hacker News 最热头条（主力，不做关键词过滤）
    hn_top = fetch_hacker_news_top()
    if hn_top:
        all_news.append(("🔥 Hacker News 最热头条", hn_top))

    # 2. Show HN 热门项目
    show_articles = fetch_show_hn()
    if show_articles:
        all_news.append(("💡 Show HN 热门项目", show_articles))

    # 3. GitHub Trending
    gh_articles = fetch_github_trending()
    if gh_articles:
        all_news.append(("📦 GitHub Trending 热门仓库", gh_articles))

    if not all_news:
        print("\n[ERROR] 所有新闻源均抓取失败，退出。")
        return 1

    # 生成 Hexo MD
    generate_hexo_post(all_news, today)

    print()
    print("=" * 60)
    print("  抓取完成！")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    exit(main())
