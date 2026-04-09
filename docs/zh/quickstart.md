---
title: 快速开始
description: 无需 API Key 即可在约五分钟内验证 Skylattice，并查看 token-enabled 工作流与样例输出。
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/quickstart/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/quickstart/
---

# 快速开始

你不需要 API Key 就能验证 Skylattice 不是“只写文档的想法仓库”。

## 三个快速结论

- 最短路径是 `install -> doctor -> pytest -> validation suite`。
- 无需 `OPENAI_API_KEY` 和 `GITHUB_TOKEN` 就能验证公开预览版本。
- 真正上 token 之前，可以先对照脱敏样例看输出形状。

## 5 分钟零凭证验证

```bash
python -m pip install -e .[dev]
python -m skylattice.cli doctor
python -m pytest -q
python tools/run_validation_suite.py
```

预期结果：`doctor` 输出类似 [doctor-output.json](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/doctor-output.json)，测试通过，validation suite 跑过 Windows-first 基线。

## 样例输出

- [Task walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.md)
- [Task inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.json)
- [Radar walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-sample.md)
- [Radar inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-run-sample.json)

