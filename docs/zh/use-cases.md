---
title: 适用场景
description: Skylattice 最适合哪些人、哪些任务，以及哪些场景暂时还不适合使用它。
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/use-cases/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/use-cases/
---

# 适用场景

Skylattice 更适合把 Agent 当成基础设施来理解的人，而不是把它当成一次性 prompt 工具的人。

## 你应该关注它，如果你想要

- 一个把私有记忆留在本地、把系统行为放在 Git 里的个人 Agent 基座
- 一个能在明确审批边界内执行 repo 任务的运行时
- 一个能从 GitHub 发现开源模式、再通过可回滚路径做有限演进的系统

## 你可以从它学到什么

- 如何把私有记忆和公开仓库状态分开
- 如何让 Agent 的动作在事后仍可审计
- 如何让 CI 和运行时验证使用同一份 tracked policy

## 暂时不适合的场景

- 想要托管式产品
- 想要零配置自主执行
- 想要 AST 级重构或任意 shell 自动化
