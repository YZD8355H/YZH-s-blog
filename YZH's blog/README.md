# YZH的Blog

纯静态技术博客：**Markdown 即文章**，深色开发者风格（Tokyo Night），零运行时依赖。

## 快速开始

```bash
uv sync          # 首次：安装依赖
uv run build.py  # 构建站点到 site/
uv run serve.py  # 本地预览 http://localhost:8000
```

一条命令构建+预览：`uv run build.py --serve`

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

3. `uv run build.py` 重新构建即可发布

## 站点配置

`config.yaml`：博客名、署名、社交链接、友链（友链页自动渲染）。

## 目录结构

```
content/posts/    文章（Markdown，丢进来即发布）
content/pages/    独立页面（about、links）
templates/        Jinja2 模板
assets/           深色主题 CSS / 搜索 JS / 图标
site/             构建产物（整个文件夹可直接部署到任意静态托管）
build.py          构建器（frontmatter 校验、代码高亮、死链检查）
serve.py          本地预览服务器
```

## 设计细节

- 代码高亮：Pygments（one-dark 主题）构建时渲染，断网可用
- 全文搜索：本地 `search-index.json` + 前端过滤，无后端无 CDN
- 深色主题：Tokyo Night 色板，终端隐喻（❯ 提示符、●●● 代码块标题栏）
- 构建时自动死链检查，frontmatter 错误会指出文件名和行号
