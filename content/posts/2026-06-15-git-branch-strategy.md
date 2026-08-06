---
title: Git 分支策略：个人项目与团队协作的实践
date: 2026-06-15
tags: [Git, 工作流]
category: 开发
summary: 分支不是越多越好。这篇讲 Git Flow、GitHub Flow 和 Trunk-Based 三种策略的取舍，以及个人项目怎么选。
---

分支策略是团队协作的地基。选错了，合并冲突会天天教做人；选对了，它安静得让人忘记它的存在。

## 三种主流策略

### GitHub Flow —— 极简主义

只有一条长期分支 `main`，所有开发在短命分支上进行：

```bash
# 从 main 拉分支
git checkout -b feature/login

# 提交、推送、开 PR 审查
git push -u origin feature/login

# 合并后删除分支
git checkout main && git pull
git branch -d feature/login
```

**适合**：持续部署的团队、个人项目。规则只有一条：`main` 永远可部署。

### Git Flow —— 完整仪式感

长期分支有 `main`（发布）和 `develop`（开发），短期分支有 `feature`、`release`、`hotfix`：

```bash
# 功能开发从 develop 分支
git checkout -b feature/xxx develop

# 发布时拉 release 分支，只修 bug 不添功能
git checkout -b release/v1.2 develop

# 线上紧急修复走 hotfix
git checkout -b hotfix/critical main
```

**适合**：有固定发布周期的产品。缺点是仪式感太强，个人项目往往用不上。

### Trunk-Based —— 主干开发

所有人在 `main` 上开发，用**短命分支 + 频繁合并**控制风险：

```bash
git checkout -b fix/typo
git commit -m "fix: 修正错别字"
git checkout main && git pull --rebase
git merge fix/typo && git push
```

**适合**：小团队、追求快速迭代。核心思想是分支存活时间不超过一两天。

## 提交信息的习惯

分支策略之外，提交信息是第二重要的习惯。约定俗成的格式：

```text
feat: 新增登录功能
fix: 修复并发下的资源泄漏
docs: 更新 README
refactor: 重构配置加载逻辑
test: 补充边界用例
```

## 我的选择

| 项目类型 | 策略 | 理由 |
|---|---|---|
| 个人博客/玩具项目 | GitHub Flow | 一条 main 走天下 |
| 开源库 | GitHub Flow + 严格 PR 审查 | 社区协作标准 |
| 有版本的商业产品 | Git Flow | release 分支天然对应版本号 |
| 3-5 人快速迭代团队 | Trunk-Based | 冲突少、合并快 |

**记住**：策略是给团队用的，不是给自己加戏的。先跑起来，再优化流程。
