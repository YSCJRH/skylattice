---
title: 应用预览
description: 用一条命令在本地预览 Skylattice 的网页产品面，查看只读示例工作区，并理解从 preview 切到 live pairing 之后会发生什么变化。
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/app-preview/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/app-preview/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice App Preview",
    "description": "Skylattice 网页产品面的只读初步预览入口。",
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.4.0",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "zh-CN"
  }
---

# 应用预览

如果你想先看看 Skylattice 的网页产品面是什么样子，而不是先配置 GitHub OAuth、pairing 本地 agent 或 hosted deployment，就从这里开始。

## 一条命令的入口

在仓库根目录执行：

```powershell
npm install
npm run web:preview
```

然后打开 [http://localhost:3000/dashboard](http://localhost:3000/dashboard)。

这会启动同仓库的 `Next.js` 应用，并以只读 preview 模式加载一套已经准备好的代表性示例数据。

Tracked proof data: [web-app-preview-state.json](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/web-app-preview-state.json)

## 你可以先看哪些页面

这个 preview 主要是为了帮你快速回答一个问题：这个网页产品面看起来是否足够可信，值得继续深入？

建议优先打开这些路由：

- `/dashboard`：设备状态、最近命令、approval 压力、memory activity
- `/tasks`：governed task run 的表面形态和代表性结果历史
- `/radar`：scan、schedule validate、replay、rollback 的工作区
- `/memory`：search、profile proposal、review-driven memory actions
- `/commands`：命令账本和单条命令 drill-down
- `/connect`：pairing flow、pairing code 和 claimed device 状态
- `/devices` 与 `/approvals`：更长期的管理页

## 这个 Preview 是什么

- 一个真实但只读的网页产品初步入口
- 一个带代表性 command、device、pairing、approval 数据的 guest session
- 一个在 live setup 之前先评估信息架构和交互模型的方式

## 这个 Preview 不是什么

- 不是 hosted runtime
- 不是 live account session
- 默认不会连到真实的本地 agent
- 不允许直接 queue live commands、revoke live devices 或 resolve live approvals

这个 preview 是刻意保持只读的。

## 切到 Live Mode 之后会变什么

当你从 preview 进入 live control，架构并不会变，只是数据从代表性样例变成真实运行面：

1. 用 GitHub 登录
2. 创建短时 pairing code
3. 在本地用 `skylattice web pair` claim 这个 code
4. 让本地 connector claim commands 并回传 readiness

浏览器仍然不会变成 runtime truth。真正执行任务、维护 memory、做审批和治理判断的，仍然是配对后的本地 Skylattice agent。

## 相关页面

- [Web Control Plane](../web-control-plane.md)
- [快速开始](quickstart.md)
- [证明材料](proof.md)
- [v0.4.0 Stable](releases/v0-4-0.md)
