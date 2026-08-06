---
title: Python 虚拟环境完全指南：从 venv 到 uv
date: 2026-07-20
tags: [Python, 教程]
category: 教程
summary: 虚拟环境是 Python 开发的第一课。这篇讲清楚它解决什么问题、标准库 venv 怎么用、以及新一代工具 uv 为什么更值得推荐。
---

在 Python 的世界里，环境隔离是每一位开发者绕不开的第一课。

## 为什么要虚拟环境

假设你同时开发两个项目：项目 A 需要 `requests 2.31`，项目 B 需要 `requests 2.28`。如果都装在系统 Python 里，它们会互相打架。虚拟环境为每个项目提供**独立的包空间**，互不干扰。

```bash
# 没有虚拟环境时，安装会污染全局
pip install requests

# 有虚拟环境时，安装只影响当前项目
.venv/bin/pip install requests
```

## 标准库方案：venv

Python 3.3+ 自带 `venv`，无需安装任何东西：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活（Windows / macOS / Linux 略有不同）
.venv\Scripts\activate      # Windows (cmd)
source .venv/bin/activate   # macOS / Linux

# 使用完毕后退出
deactivate
```

激活后，`pip` 安装的包只存在于 `.venv` 中，删除 `.venv` 文件夹即可彻底清理。

## 新一代方案：uv

`venv` 够用但繁琐 —— 激活、管理、迁移都是手工活。**uv** 用一条命令把这些全包了，而且快得惊人（Rust 编写）：

```bash
# 一条命令：创建虚拟环境 + 安装依赖
uv init my-project && cd my-project
uv add requests

# 按 pyproject.toml 恢复环境（相当于 pip install -r requirements.txt 的进化版）
uv sync

# 在环境中直接运行脚本，无需手动激活
uv run python main.py
```

uv 的 `pyproject.toml` 声明依赖：

```yaml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.31",
    "fastapi>=0.110",
]
```

## 实战建议

| 场景 | 推荐做法 |
|---|---|
| 个人小项目 | `uv init` + `uv add`，一条龙 |
| 团队协作 | `pyproject.toml` 提交进 git，同事 `uv sync` 即恢复 |
| 系统级工具 | 直接用 `uv tool install`，甚至不需要虚拟环境 |

**核心原则**：永远不要在全局环境里安装项目依赖。虚拟环境不是可选项，是基本盘。
