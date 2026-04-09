---
title: 对比定位
description: Skylattice 与通用 Agent 框架、聊天包装层、Repo 自动化 bot 和本地知识工具的核心差别。
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/comparison/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/comparison/
---

# 对比定位

Skylattice 的目标不是功能最全，而是把一个特定设计空间做清楚：本地优先记忆、受治理的 repo task，以及有边界的自我演进。

## 它比什么更强

- 比通用框架更强调审批边界和可回滚性
- 比普通 repo automation bot 更强调账本、物化 payload 和本地记忆
- 比单纯本地知识工具更强调行动和演进，而不是只做存储

## 它故意放弃了什么

- 更少的集成
- 没有托管控制面
- 没有 AST refactor 引擎
- 不承诺无人审阅的生产级自治

## 一句话定位

> 本地优先 AI Agent 运行时，强调持久记忆、受治理的仓库任务，以及 Git 原生的可审计演进。
