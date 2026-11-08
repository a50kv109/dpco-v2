# DPCO — Architecture Overview

This document is a consolidation summary authored by the VS Code Agent. It
describes the DPCO PoC v0.1 as present in this archive; it is not an original
Gemini architecture artifact.

## Conceptual flow

```text
LLM / request interpretation
          |
          v
       DPCO Core
      /    |     \
validate  Gate  Registry -> Dispatcher -> Executor
                                         |
                                         v
                                  Independent Verifier
                                         |
                                         v
                                   Result Classifier
                                         |
                                         v
                                  Execution Ledger
```

The LLM may interpret a request and propose a hypothesis. The PoC does not
implement an LLM integration; its entry point receives a structured `Task`.

## Components

- **DPCO Core** — sequences validation, contradiction checks, compatibility,
  dispatch/execution, independent verification, classification, and recording.
- **Capability Registry** — stores operation support and executor properties.
  `is_compatible` checks operation support and required exact arithmetic.
- **Dispatcher** — deterministically orders compatible production executors
  by cost and then ID. Test-only executors are excluded from normal candidates.
- **Executors** — `ExactExecutor` uses `fractions.Fraction`;
  `NumericalExecutor` uses finite floating-point values; `BadExecutor` exists
  solely for controlled verification-failure testing.
- **Independent Verifier** — checks the proposed root against the equation,
  then separately compares a supplied claim to the verified root. It does not
  accept a verdict from the executor.
- **Contradiction Gate** — checks every pair in a system using the supported
  scalar equation representation `a*x + b = c`.
- **Execution Ledger** — appends JSONL task inputs, selected executor and
  result where present, reason, timestamp, and final status fields.

## Status model

| Dimension | Values | Meaning |
|---|---|---|
| Execution | `SUCCESS`, `FAILED`, `BLOCKED` | Whether execution was performed and its technical outcome |
| Claim | `TRUE`, `FALSE`, `UNKNOWN`, `NOT_APPLICABLE` | Whether a user's supplied claim matches a checked result |
| Verification | `VERIFIED`, `UNVERIFIED`, `NOT_APPLICABLE` | Whether a verification procedure ran and its outcome |

These are independent dimensions. For example, an executor may run
successfully while its root fails verification:
`SUCCESS / UNKNOWN / UNVERIFIED`.

## Domain boundary

The PoC solves individual equations `a*x + b = c`. It checks pairwise
inconsistency in equation systems but does **not** solve consistent systems.
Those are admitted by the gate and then return `CAPABILITY_GAP`, because no
system-solving executor is registered.

## Trust boundaries and limitations

- Exact execution and exact verification both use Python `Fraction`; this is
  not full implementation independence.
- Numerical checks use configured tolerances rather than a formal proof.
- The testing-only bad executor is unavailable to ordinary dispatch but can be
  selected explicitly through `force_executor`.
- The JSONL ledger does not provide tamper evidence or multi-process locking.
