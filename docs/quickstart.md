---
title: Quick Start
description: Verify Skylattice in about five minutes with no API keys, then inspect token-enabled workflows and public-safe sample outputs.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/quickstart/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/quickstart/
---

# Quick Start

You can verify that Skylattice is real without API keys.

The no-credential path proves the runtime boots, the validation baseline is tracked, and the repository contains representative sample outputs before you trust it with real tokens.

## Key Takeaways

- The fastest success path is `install -> doctor -> pytest -> validation suite`.
- You do not need `OPENAI_API_KEY` or `GITHUB_TOKEN` to verify the public preview.
- Token-enabled runs are available after you compare your results to the redacted samples.

## 5-Minute No-Credential Path

1. Install the project.

```bash
python -m pip install -e .[dev]
```

2. Verify local runtime health.

```bash
python -m skylattice.cli doctor
```

Expected: a JSON report like [doctor-output.json](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/doctor-output.json) showing `status: ok`, the local SQLite path, and the tracked validation commands.

3. Run smoke tests and the public validation suite.

```bash
python -m pytest -q
python tools/run_validation_suite.py
```

Expected: passing tests and the Windows-first baseline from `configs/task/validation.yaml`.

4. Inspect the public-safe sample outputs.

- [Task walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.md)
- [Task inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.json)
- [Radar walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-sample.md)
- [Radar inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-run-sample.json)

## Token-Enabled Path

PowerShell example:

```powershell
$env:OPENAI_API_KEY = "..."
$env:GITHUB_TOKEN = "..."
$env:SKYLATTICE_GITHUB_REPOSITORY = "YSCJRH/skylattice"
```

Representative commands:

```bash
skylattice task run --goal "Refresh README and prepare a draft PR" --allow repo-write --allow external-write
skylattice radar scan --window weekly --limit 20
```

## Read Next

- [Proof and sample outputs](proof.md)
- [FAQ](faq.md)
- [v0.2.0 Public Preview](releases/v0-2-0.md)

