#!/usr/bin/env python3
"""
每日科技新闻自动抓取脚本
从多个免费 API 获取最新科技新闻，生成 Hexo 兼容的 Markdown 文件。

数据来源:
  - Hacker News Top Stories (hacker-news.firebaseio.com)
  - GitHub Trending (github.com/trending)

输出: source/_posts/<YYYY-MM-DD>-tech-news.md
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
MAX_NEWS_PER_SOURCE = 10  # 每个来源最多取几条
USER_AGENT = "Mozilla/5.0 (compatible; TechNewsBot/1.0)"
REQUEST_TIMEOUT = 15  # 秒

# 北京时间
TZ_BEIJING = timezone(timedelta(hours=8))

# AI 相关关键词（用于筛选 HN 文章，使用单词边界匹配避免误伤）
AI_KEYWORDS = [
    # 单字母缩写（单词边界匹配，防止误伤）
    "AI", "LLM", "AGI", "RAG", "RLHF", "TTS", "VLM",
    # 公司/产品名
    "OpenAI", "ChatGPT", "GPT-4", "GPT-5", "Claude", "Anthropic",
    "Gemini", "DeepMind", "LLaMA", "Mistral", "Copilot", "Cursor",
    "Codex", "Grok", "Perplexity", "Midjourney",
    "Stable Diffusion", "DALL-E", "Sora",
    # 技术术语（复合词优先，避免单词过宽）
    "large language model", "language model", "vision model",
    "world model", "AI agent", "AI model",
    "machine learning", "deep learning", "neural network",
    "reinforcement learning", "fine-tuning",
    "transformer", "diffusion model", "generative AI",
    "artificial intelligence",
    "text-to-speech", "speech synthesis",
    "tokenizer", "embedding model",
    "AI safety", "AI alignment", "AI regulation",
    "AI coding", "AI programming", "coding agent",
    "humanoid robot", "AI hardware", "AI chip",
    "autonomous vehicle", "self-driving",
    "vector database", "prompt engineering",
    "multi-modal", "multimodal",
    "neural", "inference engine",
]

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

def truncate(text, max_len=200):
    """截断文本，超出加省略号。"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."

# ============================================================
# 新闻源 1: Hacker News
# ============================================================

def fetch_hacker_news():
    """
    获取 Hacker News 首页热门故事。
    API: https://github.com/HackerNews/API
    """
    print("[INFO] 正在抓取 Hacker News 热门...")

    # 1. 获取 top stories ID 列表
    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        print("  [FAIL] 无法获取 Hacker News 列表")
        return []

    # 2. 逐条获取详情
    articles = []
    for item_id in ids[:MAX_NEWS_PER_SOURCE]:
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
                f"共有 **{comments}** 条评论讨论。"
            ),
            "source": "Hacker News",
        })

    print(f"  [OK] Hacker News: {len(articles)} 篇")
    return articles

# ============================================================
# 新闻源 2: AI 热点资讯（从 HN 中筛选 AI 相关文章）
# ============================================================

def fetch_ai_news():
    """
    从 Hacker News 热门中筛选 AI 相关的文章和讨论。
    获取更多文章（50 篇），按 AI 关键词匹配标题。
    """
    print("[INFO] 正在抓取 AI 热点资讯...")

    ids = fetch_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        print("  [FAIL] 无法获取 Hacker News 列表")
        return []

    articles = []
    for item_id in ids[:50]:  # 获取更多以便筛选
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        if not item:
            continue
        if item.get("type") != "story":
            continue

        title = item.get("title", "")
        title_lower = title.lower()
        # 检查标题是否包含 AI 关键词（单词边界匹配，避免误伤）
        matched = False
        for kw in AI_KEYWORDS:
            kw_lower = kw.lower()
            # 复合词（含空格）：直接用 in 匹配
            if " " in kw_lower:
                if kw_lower in title_lower:
                    matched = True
                    break
            else:
                # 单词/缩写：用正则单词边界匹配
                if re.search(r'\b' + re.escape(kw_lower) + r'\b', title_lower):
                    matched = True
                    break
        if not matched:
            continue

        url = item.get("url", f"https://news.ycombinator.com/item?id={item_id}")
        score = item.get("score", 0)
        comments = item.get("descendants", 0)
        articles.append({
            "title": title,
            "url": url,
            "summary": (
                f"该文章聚焦人工智能领域，"
                f"在 Hacker News 上获得 **{score}** 点热度，"
                f"共有 **{comments}** 条评论讨论。"
            ),
            "source": "AI 热点",
        })

        if len(articles) >= MAX_NEWS_PER_SOURCE:
            break

    print(f"  [OK] AI 热点资讯: {len(articles)} 篇")
    return articles


# ============================================================
# 新闻源 3: GitHub Trending
# ============================================================

# ============================================================
# 编程语言名称中英对照
# ============================================================

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
    # 编程语言
    if lang:
        lang_cn = LANG_NAMES.get(lang, lang)
        parts.append(f"编程语言：**{lang_cn}**")
    # Stars
    if stars:
        parts.append(f"⭐ **{stars}**")
    # 描述（英文原文）
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
        # 1. 提取仓库路径: href="/owner/repo" inside <h2 class="h3 lh-condensed">
        repo_m = re.search(
            r'<h2\s+class="h3\s+lh-condensed">\s*<a[^>]*href="/([^"]+)"[^>]*>',
            art_html,
        )
        if not repo_m:
            continue
        full_name = repo_m.group(1).strip()

        # 2. 提取描述: <p class="col-9 color-fg-muted my-1 tmp-pr-4">
        desc_m = re.search(
            r'<p\s+class="[^"]*col-9[^"]*color-fg-muted[^"]*my-1[^"]*"[^>]*>\s*(.*?)\s*</p>',
            art_html,
            re.DOTALL,
        )
        desc = desc_m.group(1).strip() if desc_m else ""
        # 清理 HTML 标签
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

        tag_parts = []
        if lang:
            tag_parts.append(f"语言: {lang}")
        if stars:
            tag_parts.append(f"⭐ {stars}")
        if desc:
            tag_parts.append(desc)

        title = f"{full_name}"
        if desc:
            title += f" — {desc}"

        articles.append({
            "title": title,
            "url": f"https://github.com/{full_name}",
            "summary": format_github_summary(lang, stars, desc),
            "source": "GitHub Trending",
        })

        if len(articles) >= MAX_NEWS_PER_SOURCE:
            break

    print(f"  [OK] GitHub Trending: {len(articles)} 篇")
    return articles

# ============================================================
# 新闻源 3: Hacker News Show HN (展示项目)
# ============================================================

def fetch_show_hn():
    """获取 Hacker News Show HN 最新展示项目。"""
    print("[INFO] 正在抓取 Show HN...")

    ids = fetch_json("https://hacker-news.firebaseio.com/v0/showstories.json")
    if not ids:
        print("  [FAIL] 无法获取 Show HN 列表")
        return []

    articles = []
    for item_id in ids[:MAX_NEWS_PER_SOURCE]:
        item = fetch_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
        if not item:
            continue
        title = item.get("title", "(无标题)")
        # Show HN 的标题通常以 "Show HN:" 开头
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
# 生成 Hexo Markdown
# ============================================================

# ============================================================
# 各类新闻源的中文简介
# ============================================================

SOURCE_INTROS = {
    "🤖 AI 热点资讯": (
        "从全球技术社区中精选的人工智能相关热门文章与讨论。"
        "涵盖大语言模型（LLM）、AI Agent、机器学习、深度学习、"
        "计算机视觉、语音合成等前沿领域，让你第一时间了解 AI 圈的最新进展与趋势。"
    ),
    "🚀 Hacker News 热门": (
        "Hacker News 是 Y Combinator 旗下的知名技术社区，由硅谷创业教父 Paul Graham 创立。"
        "这里汇集了全球开发者关注的科技话题、技术文章和行业讨论，是了解技术趋势的绝佳窗口。"
    ),
    "💡 Show HN 精选项目": (
        "Show HN 是 Hacker News 上的特色栏目，供开发者展示自己打造的项目和产品。"
        "从开源工具到创意应用，这里每天都有令人眼前一亮的创新作品涌现。"
    ),
    "📦 GitHub Trending": (
        "GitHub Trending 展示了当日最受关注的开源仓库，按 star 增长速度排序。"
        "涵盖 AI 大模型、开发工具、框架库等热门领域，是发现优秀开源项目的最佳途径。"
    ),
}


def generate_hexo_post(articles_by_source, target_date):
    """
    将新闻数据生成 Hexo 兼容的 Markdown 文件。
    每篇文章包含一级标题（H1）、中文简介，以及结构清晰的二级/三级标题，
    配合 Butterfly 主题的 toc.number 自动标号功能。

    articles_by_source: [(source_name, [articles]), ...]
    target_date: datetime.date 对象
    """
    date_str = target_date.strftime("%Y-%m-%d")
    filename = f"{date_str}-tech-news.md"
    filepath = os.path.join(BLOG_SOURCE_DIR, filename)

    total = sum(len(articles) for _, articles in articles_by_source)

    # 构建 Markdown 内容
    lines = []
    lines.append("---")
    lines.append(f"title: 每日科技新闻 - {date_str}")
    lines.append(f"date: {date_str}")
    lines.append("tags: [科技新闻, 技术资讯, HackerNews, GitHub]")
    lines.append("categories: 科技资讯")
    lines.append("---")
    lines.append("")

    # === 一级标题（必须，配合 TOC 自动标号） ===
    lines.append(f"# 每日科技新闻 - {date_str}")
    lines.append("")

    # === 概览信息 ===
    lines.append(f"> 📰 自动化抓取于 {datetime.now(TZ_BEIJING).strftime('%Y-%m-%d %H:%M')} (北京时间)")
    lines.append(f"> 📊 共收录 **{total}** 条科技新闻")
    lines.append("")

    # === 中文简介 ===
    lines.append(
        "本文每日自动汇总全球技术圈的热门资讯：优先呈现 **AI 人工智能** 领域的最新动态，"
        "随后是 **Hacker News** 与 **Show HN** 的精选讨论，最后展示 **GitHub Trending** "
        "热门开源项目，帮助你快速掌握技术前沿。"
    )
    lines.append("")

    lines.append("<!-- more -->")
    lines.append("")

    # === 各新闻源板块 ===
    for source_name, articles in articles_by_source:
        lines.append(f"## {source_name}")
        lines.append("")

        # 中文简介
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
    print("  每日科技新闻抓取")
    print(f"  运行时间: {datetime.now(TZ_BEIJING).strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
    print("=" * 60)
    print()

    today = datetime.now(TZ_BEIJING).date()

    # 抓取所有来源
    all_news = []

    # 1. AI 热点资讯（优先展示）
    ai_articles = fetch_ai_news()
    if ai_articles:
        all_news.append(("🤖 AI 热点资讯", ai_articles))

    # 收集 AI 板块已收录的 URL，避免后续板块重复
    ai_urls = {a["url"] for a in ai_articles} if ai_articles else set()

    # 2. Hacker News 热门（排除已在 AI 板块出现的文章）
    hn_articles = fetch_hacker_news()
    if hn_articles:
        hn_articles = [a for a in hn_articles if a["url"] not in ai_urls]
        if hn_articles:
            all_news.append(("🚀 Hacker News 热门", hn_articles))

    # 3. Show HN 精选项目（排除已在 AI 板块出现的项目）
    show_articles = fetch_show_hn()
    if show_articles:
        show_articles = [a for a in show_articles if a["url"] not in ai_urls]
        if show_articles:
            all_news.append(("💡 Show HN 精选项目", show_articles))

    # 4. GitHub Trending
    gh_articles = fetch_github_trending()
    if gh_articles:
        all_news.append(("📦 GitHub Trending", gh_articles))

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
