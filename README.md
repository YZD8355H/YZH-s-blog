# YZH的Blog

纯静态技术博客：**Markdown 即文章**，深色开发者风格（Tokyo Night / TERMINAL OS），零运行时依赖，断网可完整浏览。

## 快速开始

```bash
uv sync          # 首次：安装依赖（之后不用重复）
uv run build.py  # 构建站点到 site/
uv run serve.py  # 本地预览 http://localhost:8000（自动打开浏览器）
```

一条命令构建+预览：`uv run build.py --serve`

## 本地运行（详细版）

### 这台电脑上（项目已存在）

```bash
cd "项目目录"

uv sync             # 首次需要：安装依赖
uv run build.py     # 构建站点到 site/
uv run serve.py     # 启动预览 → 浏览器打开 http://localhost:8000
```

**停止预览**：终端按 `Ctrl+C`。

### 新电脑 / 重装系统后

**第 1 步 · 安装 uv**（Windows）：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

macOS / Linux：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**第 2 步 · 拉取项目**：

```bash
git clone https://github.com/YZD8355H/YZH-s-blog.git
cd YZH-s-blog
```

**第 3 步 · 构建 + 预览**：

```bash
uv sync
uv run build.py --serve
```

依赖总共 4 个 Python 包（`uv sync` 自动安装）：`markdown`、`pygments`、`jinja2`、`pyyaml`。

## 写文章

1. 在 `content/posts/` 新建 Markdown 文件，文件名建议 `YYYY-MM-DD-文章名.md`（文件名即 URL）
2. 文件头写 frontmatter：

```yaml
---
title: 文章标题
date: 2026-08-06
tags: [Python, 教程]
category: 开发
summary: 一句话摘要（可选，缺省截取正文前120字）
draft: true   # 可选：true 时跳过构建（草稿）
---
```

3. `uv run build.py` 重新构建，刷新浏览器即可看到

**小技巧**：`tags` 支持 `[A, B]` 或 `[A]`；`category` 是单值分类，显示为徽标；30 天内的新文章自动带 `NEW` 徽章。

## 站点配置

`config.yaml`：博客名、署名、社交链接（页脚）、构建参数。

## 目录结构

```
content/posts/    文章（Markdown，丢进来即发布）
content/pages/    独立页面（about 等）
templates/        Jinja2 模板
assets/           深色主题 CSS / 交互 JS / 图标
site/             构建产物（整个文件夹可直接部署到任意静态托管）
build.py          构建器（frontmatter 校验、代码高亮、死链检查、模板严格校验）
serve.py          本地预览服务器（可指定端口 -p）
DEPLOY.md         服务器部署指南（Nginx / GitHub Pages / Cloudflare）
```

## 设计细节

- 代码高亮：Pygments（one-dark 主题）构建时渲染，断网可用；代码块带 ●●● 终端标题栏和复制按钮
- 全文搜索：本地 `search-index.json` + 前端过滤，无后端无 CDN
- 视觉：Tokyo Night 色板、网格背景、终端 Hero（打字机）、git-log 时间线文章列表、码字点击粒子、滚动进度条、回到顶部
- 构建时自动死链检查；frontmatter 错误会指出文件名和行号；模板变量缺失直接报错（StrictUndefined）
