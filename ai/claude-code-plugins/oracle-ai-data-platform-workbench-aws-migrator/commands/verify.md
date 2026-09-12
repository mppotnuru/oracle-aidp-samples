---
description: Classify a migration's output as PASS / REVIEW / SKIP / FAIL
argument-hint: <migrated/ or report.json> [--filter athena|glue]
allowed-tools: Bash(aws-aidp verify:*), Bash(python3 -m aws_aidp.cli verify:*)
---

Classify the outcome of a migration:

`aws-aidp verify $ARGUMENTS`

After it runs, report the PASS / REVIEW / SKIP / FAIL counts and the per-asset list.
Explain what each means: PASS = auto-translated and runnable; REVIEW = translated but
has flags a human must check; SKIP = translator not built yet (EMR/SageMaker are on the
roadmap); FAIL = translation error. A non-zero FAIL count is the only hard failure.
