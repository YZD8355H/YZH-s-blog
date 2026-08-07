#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YZH的Blog 构建器
用法:
    uv run build.py            # 构建静态站点到 site/
    uv run build.py --serve    # 构建并启动本地预览服务器
    uv run build.py --clean    # 先清空 site/ 再构建

约定:
    content/posts/*.md    文章（frontmatter: title/date/tags/category/summary/draft）
    content/pages/*.md    独立页面（about/links 等）
"""
import argparse
import datetime as dt
import html as html_lib
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import quote, unquote

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parent
ERRORS: list[str] = []
WARNINGS: list[str] = []

HIGHLIGHT_STYLE = "one-dark"   # 代码高亮主题（深色系，与站点风格一致）


def error(msg: str) -> None:
    ERRORS.append(msg)
    print(f"  ✗ {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  ⚠ {msg}")


# ---------------------------------------------------------------- 配置
def load_config() -> dict:
    path = ROOT / "config.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    site = cfg.get("site", {}) or {}
    build = cfg.get("build", {}) or {}
    return {
        "site": {
            "title": site.get("title", "YZH的Blog"),
            "author": site.get("author", "YZH"),
            "description": site.get("description", ""),
            "since": site.get("since", dt.date.today().year),
            "language": site.get("language", "zh-CN"),
        },
        "social": cfg.get("social", {}) or {},
        "links": cfg.get("links", []) or [],
        "build": {
            "posts_per_page": int(build.get("posts_per_page", 8)),
            "site_dir": build.get("site_dir", "site"),
        },
    }


# ---------------------------------------------------------------- Markdown
def make_markdown():
    return markdown.Markdown(
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
        output_format="html5",
    )


CODEBLOCK_RE = re.compile(
    r"<pre(?P<pre_attrs>[^>]*)><code(?P<code_attrs>[^>]*)>(?P<code>.*?)</code></pre>",
    re.DOTALL,
)
LANG_RE = re.compile(r'class="language-([\w#.+-]+)"')

# 代码块标题栏的"文件名"提示（模拟真实终端/编辑器打开的文件）
LANG_FILE_HINTS = {
    "python": "script.py", "py": "script.py",
    "bash": "script.sh", "sh": "script.sh", "shell": "script.sh", "console": "terminal",
    "yaml": "config.yaml", "yml": "config.yml",
    "json": "config.json", "javascript": "app.js", "js": "app.js",
    "typescript": "app.ts", "ts": "app.ts", "jsx": "App.jsx", "tsx": "App.tsx",
    "html": "index.html", "css": "style.css", "scss": "style.scss",
    "sql": "query.sql", "java": "Main.java", "c": "main.c", "cpp": "main.cpp",
    "csharp": "Program.cs", "go": "main.go", "rust": "main.rs", "ruby": "main.rb",
    "php": "index.php", "markdown": "README.md", "md": "README.md",
    "docker": "Dockerfile", "dockerfile": "Dockerfile", "nginx": "nginx.conf",
    "git": ".gitconfig", "diff": "changes.diff", "xml": "config.xml",
    "toml": "pyproject.toml", "ini": "config.ini", "text": "notes.txt",
    "makefile": "Makefile", "cmake": "CMakeLists.txt", "powershell": "setup.ps1",
    "kotlin": "Main.kt", "swift": "main.swift", "lua": "main.lua", "perl": "script.pl",
}


def highlight_code(code: str, lang: str | None) -> str:
    if lang:
        try:
            lexer = get_lexer_by_name(lang, stripall=True)
        except ClassNotFound:
            lexer = TextLexer(stripall=True)
    else:
        lexer = TextLexer(stripall=True)
    return pyg_highlight(code, lexer, HtmlFormatter(nowrap=True))


def transform_codeblocks(html_text: str) -> str:
    """fenced code 输出 → 终端风格代码块（●●● 标题栏 + Pygments 高亮）"""

    def repl(m: re.Match) -> str:
        lm = LANG_RE.search(m.group("code_attrs"))
        lang = lm.group(1) if lm else None
        label = lang or "text"
        fname = LANG_FILE_HINTS.get(label, "")
        code = html_lib.unescape(m.group("code"))
        body = highlight_code(code, lang)
        bar = (
            '<div class="codeblock-bar">'
            '<span class="cb-tab"><i class="cb-tab-dot"></i>'
            f'<span class="cb-filename">{html_lib.escape(fname or label)}</span></span>'
            f'<span class="cb-lang">{html_lib.escape(label)}</span>'
            '<span class="win-btns">'
            '<span class="wb" aria-hidden="true">─</span>'
            '<span class="wb" aria-hidden="true">□</span>'
            '<span class="wb wb-close" aria-hidden="true">✕</span>'
            "</span>"
            "</div>"
        )
        return f'<div class="codeblock">{bar}<div class="highlight">{body}</div></div>'

    return CODEBLOCK_RE.sub(repl, html_text)


def md_to_html(md, text: str) -> str:
    return transform_codeblocks(md.reset().convert(text))


def strip_html(html_text: str) -> str:
    text = re.sub(r"<[^>]+>", "", html_text)
    return html_lib.unescape(text)


# ---------------------------------------------------------------- frontmatter
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-?(.*)\.md$")
# Windows 文件名非法字符（标签会用作目录名）
INVALID_TAG_CHARS = set('<>:"/\\|?*')
NEW_POST_DAYS = 30  # 距发布多少天内标记为 NEW


def parse_frontmatter(path: Path):
    """返回 (fm dict, 正文, 错误或None)。错误已带文件定位。"""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text, f"{path.name}: 缺少 --- frontmatter 头"
    lines = text.splitlines()
    end = None
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None, text, f"{path.name}: frontmatter 未闭合（缺第二个 ---）"
    fm_text = "\n".join(lines[1:end - 1])
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        line = getattr(e, "problem_mark", None)
        where = f"第 {line.line + 2} 行" if line else "未知位置"
        return None, text, f"{path.name}: frontmatter YAML 解析失败（{where}）: {e.problem}"
    if not isinstance(fm, dict):
        return None, text, f"{path.name}: frontmatter 必须是键值对"
    return fm, "\n".join(lines[end:]).lstrip("\n"), None


def parse_date(value, path: Path, field="date") -> dt.date | None:
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value).strip())
    except ValueError:
        error(f"{path.name}: {field} 格式错误 {value!r}（应为 YYYY-MM-DD）")
        return None


def slugify(name: str) -> str:
    """文件名 → URL slug：去日期前缀、去扩展名。"""
    m = DATE_RE.match(name)
    if m:
        return m.group(4) or m.group(1) + m.group(2) + m.group(3)
    return name[:-3] if name.endswith(".md") else name


def load_posts(content_dir: Path, md) -> list[dict]:
    posts = []
    seen_slugs: dict[str, Path] = {}
    for path in sorted(content_dir.glob("*.md")):
        fm, body, err = parse_frontmatter(path)
        if err:
            error(err)
            continue
        title = (fm.get("title") or "").strip()
        if not title:
            error(f"{path.name}: 缺少必填字段 title")
            continue

        # 日期：frontmatter 优先，否则取文件名日期前缀
        date = parse_date(fm.get("date"), path) if fm.get("date") else None
        m = DATE_RE.match(path.name)
        fname_date = None
        if m:
            try:
                fname_date = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except ValueError:
                error(f"{path.name}: 文件名日期前缀无效")
        if date and fname_date and date != fname_date:
            error(f"{path.name}: frontmatter 日期 {date} 与文件名日期 {fname_date} 不一致")
            continue
        date = date or fname_date
        if date is None:
            error(f"{path.name}: 缺少日期（frontmatter date 或文件名 YYYY-MM-DD- 前缀）")
            continue

        if fm.get("draft"):
            print(f"  … 跳过草稿: {path.name}")
            continue

        slug = slugify(path.name)
        if slug in seen_slugs:
            error(f"{path.name}: slug 与 {seen_slugs[slug].name} 重复")
            continue
        seen_slugs[slug] = path

        tags = fm.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        tags = [{"name": str(t).strip(), "url": quote(str(t).strip(), safe="")}
                for t in tags if str(t).strip()]
        bad_tags = [t["name"] for t in tags if set(t["name"]) & INVALID_TAG_CHARS]
        if bad_tags:
            error(f"{path.name}: 标签含非法字符（标签会作为目录名）: {', '.join(bad_tags)}")
            tags = [t for t in tags if not (set(t["name"]) & INVALID_TAG_CHARS)]

        md.reset()
        html_body = transform_codeblocks(md.convert(body))
        toc = md.toc_tokens or []
        text = strip_html(html_body)
        summary = (fm.get("summary") or "").strip() or (text[:120] + ("…" if len(text) > 120 else ""))

        posts.append({
            "slug": slug,
            "file": path.name,
            "title": title,
            "date": date,
            "date_str": date.isoformat(),
            "year": date.year,
            "is_new": 0 <= (dt.date.today() - date).days <= NEW_POST_DAYS,
            "tags": tags,
            "category": (fm.get("category") or "").strip(),
            "summary": summary,
            "html": html_body,
            "toc": toc,
            "text": text,
            "url": f"posts/{quote(slug)}.html",
        })
    posts.sort(key=lambda p: (p["date"], p["file"]), reverse=True)
    return posts


def load_pages(content_dir: Path, md) -> list[dict]:
    pages = []
    for path in sorted(content_dir.glob("*.md")):
        fm, body, err = parse_frontmatter(path)
        if err:
            error(err)
            continue
        slug = path.name[:-3]
        title = (fm.get("title") or slug).strip()
        pages.append({
            "slug": slug,
            "title": title,
            "html": md_to_html(md, body),
            "url": f"{quote(slug)}/",
        })
    return pages


# ---------------------------------------------------------------- 构建
def build_pages(posts, pages, config) -> list[dict]:
    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html", "xml"]),
        undefined=StrictUndefined,  # 模板变量缺失/拼错 → 构建直接报错，防止静默产出坏页面
    )
    site_cfg = config["site"]
    social = config["social"]
    per_page = config["build"]["posts_per_page"]

    # 标签统计
    tag_posts: dict[str, list[dict]] = {}
    for p in posts:
        for t in p["tags"]:
            tag_posts.setdefault(t["name"], []).append(p)

    ctx_base = {
        "site": site_cfg,
        "social": social,
        "nav_pages": pages,
        "post_count": len(posts),
        "build_time": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    # 标签统计（首页标签墙 / 标签页共用）
    tag_posts: dict[str, list[dict]] = {}
    for p in posts:
        for t in p["tags"]:
            tag_posts.setdefault(t["name"], []).append(p)
    tag_items = [
        ({"name": name, "url": quote(name, safe="")}, ps)
        for name, ps in tag_posts.items()
    ]
    tag_items.sort(key=lambda kv: kv[0]["name"])
    generated = []  # [(相对路径, 模板名)]

    def render_to(rel_path: Path, template: str, ctx: dict):
        out = site_dir / rel_path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(env.get_template(template).render(**ctx), encoding="utf-8")
        generated.append((rel_path, template))

    # ---- 首页 + 分页
    n = len(posts)
    total_pages = max(1, (n + per_page - 1) // per_page)
    for page_no in range(1, total_pages + 1):
        chunk = posts[(page_no - 1) * per_page: page_no * per_page]
        prev_no, next_no = (page_no - 1) if page_no > 1 else None, (page_no + 1) if page_no < total_pages else None
        rel = Path("index.html") if page_no == 1 else Path(f"page/{page_no}/index.html")
        render_to(rel, "index.html", {
            **ctx_base, "root": "." if page_no == 1 else "../..",
            "posts": chunk, "total_posts": n, "tag_items": tag_items,
            "page_no": page_no, "total_pages": total_pages,
            "prev_no": prev_no, "next_no": next_no,
        })

    # ---- 文章页（含上一篇/下一篇）
    for i, p in enumerate(posts):
        prev_p = posts[i + 1] if i + 1 < len(posts) else None
        next_p = posts[i - 1] if i > 0 else None
        render_to(Path("posts") / f"{quote(p['slug'])}.html", "post.html", {
            **ctx_base, "root": "..",
            "post": p, "prev": prev_p, "next": next_p,
        })

    # ---- 归档页
    by_year: dict[int, list[dict]] = {}
    for p in posts:
        by_year.setdefault(p["year"], []).append(p)
    render_to(Path("archive/index.html"), "archive.html", {
        **ctx_base, "root": "..",
        "by_year": sorted(by_year.items(), reverse=True),
    })

    # ---- 标签云 + 每个标签的列表页
    render_to(Path("tags/index.html"), "tags.html", {
        **ctx_base, "root": "..", "tag_items": tag_items,
    })
    for tag, tag_ps in tag_items:
        render_to(Path("tags") / tag["name"] / "index.html", "tag.html", {
            **ctx_base, "root": "../..",
            "tag": tag, "posts": tag_ps,
        })

    # ---- 搜索页 + 索引
    render_to(Path("search/index.html"), "search.html", {
        **ctx_base, "root": "..",
    })
    index = {
        "posts": [
            {"title": p["title"], "url": "../" + p["url"], "date": p["date_str"],
             "tags": p["tags"], "category": p["category"],
             "summary": p["summary"], "text": p["text"]}
            for p in posts
        ]
    }
    (ROOT / site_dir / "search-index.json").write_text(
        json.dumps(index, ensure_ascii=False), encoding="utf-8")

    # ---- 独立页面
    for pg in pages:
        render_to(Path(pg["slug"]) / "index.html", "page.html", {
            **ctx_base, "root": "..", "page": pg,
            "link_items": config["links"],
        })

    # ---- 404 页（终端风：command not found）
    render_to(Path("404.html"), "404.html", {
        **ctx_base, "root": ".",
    })

    return generated


def copy_assets(site_dir: Path) -> None:
    src = ROOT / "assets"
    dst = site_dir / "assets"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    # 生成代码高亮 CSS（与站点风格匹配的深色主题）
    css = HtmlFormatter(style=HIGHLIGHT_STYLE).get_style_defs(".highlight")
    (dst / "highlight.css").write_text(css, encoding="utf-8")


def copy_content_assets(content_dir: Path, site_dir: Path) -> None:
    """复制文章引用的本地资源：
    content/images/  → site/images/     （文章里写 ../images/xxx.png）
    content/posts/ 下的子目录 → site/posts/ 对应位置（文章里写 images/xxx.png）"""
    src = content_dir / "images"
    if src.exists():
        shutil.copytree(src, site_dir / "images", dirs_exist_ok=True)
        print(f"  复制内容图片: content/images/ → images/")
    posts_src = content_dir / "posts"
    if posts_src.exists():
        for item in sorted(posts_src.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                shutil.copytree(item, site_dir / "posts" / item.name, dirs_exist_ok=True)
                print(f"  复制文章附件: posts/{item.name}/ → posts/{item.name}/")


def check_links(site_dir: Path) -> None:
    LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
    problems = []
    for html_file in site_dir.rglob("*.html"):
        base = html_file.parent
        for m in LINK_RE.finditer(html_file.read_text(encoding="utf-8")):
            u = m.group(1)
            if u.startswith(("#", "/", "http://", "https://", "mailto:", "tel:", "//", "data:")):
                continue
            if "?" in u:
                u = u.split("?")[0]
            target = (base / unquote(u)).resolve()
            if not target.exists():
                problems.append(f"{html_file.relative_to(site_dir)} → {u}")
    for prob in problems:
        error(f"死链: {prob}")
    return problems


# ---------------------------------------------------------------- main
def main() -> int:
    global site_dir
    ap = argparse.ArgumentParser(description="YZH的Blog 构建器")
    ap.add_argument("--clean", action="store_true", help="构建前清空输出目录")
    ap.add_argument("--serve", action="store_true", help="构建后启动本地预览")
    args = ap.parse_args()

    config = load_config()
    site_dir = ROOT / config["build"]["site_dir"]

    if args.clean and site_dir.exists():
        shutil.rmtree(site_dir)
        print("已清空输出目录")

    print("≡ 构建开始")
    md = make_markdown()
    posts = load_posts(ROOT / "content" / "posts", md)
    pages = load_pages(ROOT / "content" / "pages", md)

    if not posts:
        warn("posts 目录为空 —— 站点将以空列表呈现")

    generated = build_pages(posts, pages, config)
    copy_assets(site_dir)
    copy_content_assets(ROOT / "content", site_dir)
    print(f"  生成 {len(generated)} 个页面，文章 {len(posts)} 篇，标签 {len({t['name'] for p in posts for t in p['tags']})} 个")
    check_links(site_dir)

    if ERRORS:
        print(f"\n✗ 构建失败：{len(ERRORS)} 个错误")
        return 1
    print(f"\n✓ 构建完成 → {site_dir.relative_to(ROOT)}/")
    if WARNINGS:
        print(f"  （{len(WARNINGS)} 条警告，不影响产出）")
    if args.serve:
        import serve
        serve.main(port=None, directory=site_dir, open_browser=True)
    return 0


site_dir: Path = ROOT / "site"

if __name__ == "__main__":
    sys.exit(main())
