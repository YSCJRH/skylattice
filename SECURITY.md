# Security Policy

Skylattice is a local-first agent system. Please avoid putting secrets, local logs, memory exports, or private runtime artifacts into public issues or pull requests.

## Supported Surface

The actively maintained surface is the current `main` branch.

Security-sensitive areas include:

- credential handling for `OPENAI_API_KEY` and `GITHUB_TOKEN`
- GitHub write adapters and approval gates
- local memory storage and export boundaries
- destructive action protections and freeze mode
- radar promotion and rollback safety controls

## Reporting a Vulnerability

Please use a private reporting path.

- If GitHub private vulnerability reporting is enabled for this repository, use that channel.
- Otherwise contact the repository owner through GitHub first and wait for a private channel before sharing details.
- Do not post secrets, tokens, local filesystem paths, database files, or private memory excerpts in a public issue.

## Safe Disclosure Checklist

- describe the impact clearly
- provide the smallest reproducible example you can
- redact tokens, logs, and personal data before sharing anything
- mention whether the issue affects task execution, radar promotion, memory isolation, or governance enforcement