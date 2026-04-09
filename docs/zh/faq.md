---
title: 常见问题
description: 用真实问题解释 Skylattice 是什么、适合谁、如何验证以及它与通用 Agent 框架的差别。
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/faq/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/faq/
---

# 常见问题

## Skylattice 适合什么场景？

适合想研究本地优先 Agent 基础设施、持久记忆、受治理 repo task，以及 Git 审阅边界的人。

## Skylattice 是通用 coding agent 框架吗？

不是。它比通用框架更窄，但更强调 inspectability、governance 和 rollback。

## 不配 API Key 能验证吗？

可以。按 [快速开始](quickstart.md) 跑 `doctor`、测试和 validation suite 即可。

## 它会把记忆写进 Git 吗？

不会。私有记忆在 `.local/`，Git 里保留的是文档、配置、提示词和可审计系统行为。

## 它是托管产品吗？

不是。它目前是一个本地优先的 early public preview。
