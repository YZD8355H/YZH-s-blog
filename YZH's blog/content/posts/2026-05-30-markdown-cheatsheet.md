---
title: Markdown 写作速查：本站支持的语法
date: 2026-05-30
tags: [Markdown, 写作]
category: 教程
summary: 一篇覆盖本站所有 Markdown 语法的速查文章，写文章时可以直接复制参考。
---

写文章时经常要查语法，这里把本站支持的全部 Markdown 语法汇总成一张速查表，随时复制参考。

## 标题

```markdown
# 一级标题
## 二级标题
### 三级标题
```

## 文字样式

**加粗**、*斜体*、~~删除线~~、`行内代码`、[链接](https://example.com)。

## 列表

```markdown
- 无序列表项
- 另一个列表项
  - 嵌套项

1. 有序列表项
2. 按顺序排列
```

## 引用

```markdown
> 这是一段引用。
> 支持多行。
```

> 这是一段引用。
> 支持多行。

## 表格

```markdown
| 语法 | 说明 |
| --- | --- |
| `**粗**` | 加粗 |
| `\`code\`` | 行内代码 |
```

| 语法 | 说明 |
| --- | --- |
| `**粗**` | 加粗 |
| `code` | 行内代码 |

## 代码块

代码块用三个反引号包裹，可以指定语言获得语法高亮：

```python
def greet(name: str) -> str:
    """终端风格代码块 + Pygments 高亮"""
    return f"你好，{name}！"
```

```bash
# 终端命令
uv run build.py && uv run serve.py
```

```json
{
  "title": "YZH的Blog",
  "theme": "tokyo-night"
}
```

不指定语言也可以，会按纯文本显示。

## 分隔线与转义

```markdown
---

\# 反斜杠转义，可以输出字面量
```

## 小技巧

- frontmatter 的 `summary` 会显示在文章列表，建议写一句话摘要
- 不写 `summary` 时自动截取正文前 120 字
- 标签用 `tags: [A, B]` 或 `tags: [A]` 都可以
- 想存草稿，把 `draft: true` 写上，构建时会自动跳过
