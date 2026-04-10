---
title: Quick Start
description: Verify Skylattice in about five minutes with no API keys, then inspect token-enabled workflows and public-safe sample outputs.
robots: index, follow
alternates:
  - lang: en
    href: https://yscjrh.github.io/skylattice/quickstart/
  - lang: zh-CN
    href: https://yscjrh.github.io/skylattice/zh/quickstart/
jsonld: |
  {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "name": "Skylattice",
    "description": "Verify Skylattice without API keys, then inspect proof artifacts and token-enabled workflows.",
    "codeRepository": "https://github.com/YSCJRH/skylattice",
    "softwareVersion": "0.2.2",
    "license": "https://github.com/YSCJRH/skylattice/blob/main/LICENSE",
    "inLanguage": "en"
  }
---

# Quick Start

If you want to verify Skylattice without API keys, this is the page to use.

The zero-credential path proves the runtime boots, the tracked validation commands are real, and the repository contains public-safe proof artifacts before you trust it with real tokens.

## Key Takeaways

- The fastest success path is `install -> doctor -> pytest -> validation suite`.
- You do not need `OPENAI_API_KEY` or `GITHUB_TOKEN` to verify the stable public release.
- The expected outputs are documented, so you can compare your local results with public-safe samples.

## 5-Minute No-Credential Verification

1. Install the project.

```bash
python -m pip install -e .[dev]
```

2. Verify local runtime health.

```bash
python -m skylattice.cli doctor
```

Expected: a JSON report like [doctor-output.json](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/doctor-output.json) showing `status: ok`, the local SQLite path, and the tracked validation commands.

3. Run smoke tests.

```bash
python -m pytest -q
```

Expected: the repository smoke tests pass without requiring cloud credentials.

4. Run the public validation suite.

```bash
python tools/run_validation_suite.py
```

Expected: the Windows-first validation baseline from `configs/task/validation.yaml` passes and reports the same tracked commands that CI uses.

5. Inspect public-safe sample outputs.

- [Task walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.md)
- [Task inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/task-run-sample.json)
- [Radar walkthrough](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-sample.md)
- [Radar inspect JSON](https://github.com/YSCJRH/skylattice/blob/main/examples/redacted/radar-run-sample.json)

## Success Criteria

You have a believable first-run result when:

- `doctor` reports `status: ok`
- the smoke tests and validation suite pass locally
- the sample JSON structures look consistent with your local outputs

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

- [Proof](proof.md)
- [FAQ](faq.md)
- [v0.2.2 Stable](releases/v0-2-2.md)
