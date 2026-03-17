---
name: skill-mass-triage
description: "[Skill] Batch-triage LISA test failures from a run directory — diagnose with parallel sub-agents, bucketize by root cause, and produce a consolidated summary. Use when asked to triage a LISA test run. Triggers: batch triage, mass triage, triage test results, bucketize failures, lisa triage all."
---

# Batch LISA Test Triage

Triage failed tests from a LISA run directory. Diagnose each failure using sub-agents, bucketize by root cause, and produce a consolidated summary. This workflow handles any number of failures — from 1 to hundreds — using the same sub-agent dispatch pattern throughout.

## Input Format

The input is a LISA run directory containing test results. The run directory path follows this pattern:
```
<lisa-root>/runtime/log/<date>/<run-id>/
```

The run directory contains:
- `lisa-<run-id>.log` — Main log with all test results and the final summary
- `lisa.html` — HTML report (same data, formatted)
- `tests/` — Per-test directories, each with a detailed log file

To extract failed tests, parse the main log for lines matching:
```
result: FAILED
```

Each such line contains the test name (in `lisa.case[<test_name>]`), elapsed time, and environment.

For the `RootRunner` summary at the end of the main log, each failed test has a one-line summary:
```
SuiteName.test_case_name: FAILED   failed. <ExceptionType>: <message>
```

To map test names to their per-test log directories:
```bash
ls <run-dir>/tests/ | grep <test_name>
```

Each per-test directory `tests/<timestamp>-<test_name>/` contains a single log file `<timestamp>-<test_name>.log` with the full execution trace and failure details.

## Workflow

### Phase 1 — Diagnose (parallel sub-agents)

> **STOP — READ THIS FIRST.** You are the **orchestrator**. Your ONLY job in this phase is to:
> 1. Parse the main log to extract failed test names and their per-test log paths
> 2. Create the output directory
> 3. Partition failures into batches and write batch files
> 4. Generate the sub-agent prompt `.md` file
> 5. Spawn sub-agents to do the actual diagnosis
>
> **Do NOT read individual test logs, investigate failures, or do any diagnostic work yourself.** That is the sub-agents' job. If you catch yourself reading per-test log files or analyzing error messages — you have gone off-script. Stop and spawn a sub-agent instead.

> **IMPORTANT:** Always save diagnostic instructions as a `.md` file in the working directory and reference it by path when spawning sub-agents — do NOT pass full prompt text inline in `runSubagent` calls. This ensures sub-agents can read instructions with file tools, avoids context window bloat in the orchestrator, and persists the instructions for debugging.

1. Identify the LISA run directory. Confirm it exists and contains the expected structure (`lisa-*.log`, `tests/` directory).

2. Parse the main log to extract failed tests:
   ```bash
   # Get all failed test names, suite names, and short error messages
   grep -a "RootRunner.*FAILED" <run-dir>/lisa-<run-id>.log
   ```
   For each failed test, also find the per-test log directory:
   ```bash
   ls <run-dir>/tests/ | grep <test_name>
   ```

3. Create the triage output directory: `base/build/work/scratch/triage/`.
   - Ensure there are no existing JSON files from previous runs. If there are, prompt the user to confirm deletion.

4. Use cmdline tools (jq, python, etc.) to partition the failed tests into batches of **~6 tests each**, writing a JSON file per batch to the triage directory (e.g., `base/build/work/scratch/triage/batch-1.json`, `batch-2.json`, etc.) with this structure:

> **All temporary and intermediate files** (working files, batch files, etc.) MUST go in `base/build/work/scratch/triage/` — do NOT use `/tmp` or bare `mktemp -d`.

```json
{
  "runDir": "/path/to/lisa/run/dir",
  "tests": [
    {
      "testName": "verify_deployment_provision_sriov",
      "fullName": "Provisioning.verify_deployment_provision_sriov",
      "testDir": "20260306-192326-094-verify_deployment_provision_sriov",
      "shortError": "failed. NotImplementedError: "
    },
    ...
  ]
}
```

Use your best judgement on batch size, but ~6 should be the maximum. Maximize parallelism (more smaller batches) while keeping batch size manageable.

> For example, if there are 14 failed tests, create 7 batches of 2 tests each rather than 2 batches of 7.

5. For each batch, spawn a sub-agent using `runSubagent`. **Launch sub-agents in parallel if the platform supports it, BUT limit to 10 parallel sub-agents per wave** (if there are more than 10 batches, launch them in successive waves of 10). Each sub-agent receives:
   - The LISA run directory path
   - The path to its batch file
   - The output directory path
   - The path to the `.md` prompt file (do NOT inline the prompt content — reference by file path only)

> **IMPORTANT:** Always use a sub-agent — even for a single test. Do NOT diagnose failures inline in the orchestrator. Sub-agents stay scoped to categorization because they follow the prompt `.md` file; the orchestrator tends to over-investigate when it handles diagnosis directly. The orchestrator's job is strictly orchestration: partition, dispatch, collect, bucketize.

6. Each sub-agent writes one JSON file per test to the triage directory: `base/build/work/scratch/triage/<testName>.json`

7. After all sub-agents complete, verify that a JSON file exists for each failed test. Re-run any missing ones.

### Phase 2 — Bucketize & Summarize (single pass)

1. Read all `*.json` files from `base/build/work/scratch/triage/` (excluding `batch-*.json`).
2. Collect the free-form `failureCategory` values assigned by sub-agents.
3. Normalize similar categories into canonical buckets (e.g., "not-implemented-error", "platform feature missing", "sriov not supported" → **"platform-not-implemented"**). Use your judgment — the goal is <= ~15 distinct buckets. Use concise, descriptive bucket names that balance specificity and generality.
4. Write the consolidated summary to `./triage-summary.json` with this structure:

```json
{
  "generated": "2026-03-06T...",
  "runDir": "<LISA run directory path>",
  "totalTests": 91,
  "failedTests": 14,
  "passedTests": 24,
  "skippedTests": 53,
  "buckets": [
    {
      "name": "platform-not-implemented",
      "description": "Test calls a feature method not implemented for the 'ready' platform (e.g., SR-IOV, SerialConsole)",
      "count": 4,
      "tests": [
        {
          "testName": "verify_deployment_provision_sriov",
          "fullName": "Provisioning.verify_deployment_provision_sriov",
          "shortSummary": "get_nic_count() raises NotImplementedError on ready platform"
        },
        ...
      ]
    },
    ...
  ],
  "undiagnosed": []
}
```

5. Clean up triage scratch files (but only after the summary is written, in case you need to re-run any sub-agents).
6. Present a human-readable summary to the user: bucket name, count, and representative example for each.

---

## Sub-Agent Prompt Template

Use this as the prompt template when spawning diagnostic sub-agents. Save a single copy of this prompt as a `.md` file into the working directory (e.g., `base/build/work/scratch/triage/diagnose-prompt.md`) and reference it in the `runSubagent` calls, passing the variables during the call to runSubagent.

```
You are diagnosing LISA test failures for Azure Linux. For each test below, investigate the failure and write a JSON summary file.

## Inputs from the orchestrator
- LISA run directory: {{RUN_DIR}}
- Batch file path: {{BATCH_FILE}} (contains a JSON object with `runDir` and `tests` array)
- Output directory: {{OUTPUT_DIR}}

## Investigation procedure
Read the skill file at `.github/skills/skill-koji-triage/SKILL.md` for the full investigation
workflow — including how to read LISA logs and categorize failures. Follow it exactly.

## Setup
1. Read `.github/skills/skill-koji-triage/SKILL.md` (MUST do this first — despite the name, it contains the LISA triage workflow).
2. Read the batch file to get the list of tests to diagnose.

## Tasks to diagnose
Read the batch file at: {{BATCH_FILE}}
It contains a JSON object with:
- `runDir` — the LISA run directory path
- `tests` — an array of `{ "testName", "fullName", "testDir", "shortError" }` objects

## For each test
1. Find the per-test log directory: `{{RUN_DIR}}/tests/<testDir>/`
2. Read the test's log file (the single `.log` file in that directory). Focus on:
   - The tail of the log (last 80-100 lines) for the error/traceback
   - Any `ERROR` lines, Python tracebacks, command failures
   - The `result: FAILED` line and any preceding error context
3. Identify the failure category. Use a short kebab-case string (e.g., "platform-not-implemented", "missing-package", "config-mismatch", "kernel-module-missing", "network-ssl-error", "test-framework-error"). Be specific but consistent.
   - Note: Your job is JUST to categorize the failure, not to propose a fix or root cause analysis. The category should be based on the observed symptoms and error messages, not assumptions about the underlying issue.
4. Write a JSON file to: {{OUTPUT_DIR}}/<testName>.json

## Output JSON schema (one file per test)
{
  "testName": "<test case name>",
  "fullName": "<SuiteName.test_case_name>",
  "testDir": "<timestamp-test_name directory name>",
  "failureCategory": "<short-kebab-case-category>",
  "failurePhase": "<setup|execution|teardown|framework>",
  "exception": "<exception class name, e.g. NotImplementedError, AssertionError>",
  "shortSummary": "<1-2 sentence human-readable summary>"
}

## Rules
- Read only the files within the LISA run directory — do NOT modify any files outside your assigned output JSON files.
- If a test log is very large, focus on the tail (last 100 lines) where the error typically appears.
- If you can't determine the failure, set failureCategory to "unknown" and explain in shortSummary.
- Return a brief summary of findings when done (which tests succeeded/failed diagnosis).


---

## Notes

- The orchestrator handles partitioning, sub-agent dispatch, result collection, bucketization, and cleanup.
- Sub-agents handle only log reading / failure analysis / JSON writing — they read from the local filesystem, no network tools needed.
- If a sub-agent fails or hangs, note the affected test names and retry them individually.
- Clean up triage scratch files only after the final summary is written.
