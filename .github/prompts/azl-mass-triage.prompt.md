---
description: "Triage LISA test failures from a run directory — diagnose, bucketize, and summarize"
agent: agent
argument-hint: Path to a LISA run directory (e.g., /path/to/lisa-test/runtime/log/<date>/<run-id>)
---

# Batch LISA Test Triage

- **Run directory**: `${input:run_dir:path to LISA run directory}`

Follow the [skill-mass-triage skill](../skills/skill-mass-triage/SKILL.md) to triage all failed tests in `${input:run_dir}`.

Pass the run directory path to the skill workflow. You will be acting as an orchestrator here, so even though you have the skills to diagnose test failures directly you should NOT do that work yourself. Instead, follow the instructions in the skill file on how to coordinate other agents.
