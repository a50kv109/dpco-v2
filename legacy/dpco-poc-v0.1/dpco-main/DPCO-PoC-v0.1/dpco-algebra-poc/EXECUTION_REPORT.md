# DPCO PoC v0.1 — Execution Report

## Environment

- Python: `Python 3.12.3` (`python3 --version`)
- Operating environment: current VS Code Linux workspace
- DPCO project: `dpco-algebra-poc/`

## Status

| Status | Result | Evidence |
|---|---|---|
| `STATICALLY REVIEWED` | PASS | Source and supplied Iteration 02 materials were inspected; see `ENGINEERING_AUDIT.md`. |
| `GENERATOR_SYNTAX_CHECKED` | PASS | `python3 -m py_compile generate_and_run.py` exited 0. |
| `PROJECT_GENERATED` | PASS | `python3 generate_and_run.py` wrote the package and test runner. |
| `GENERATED_MODULES_SYNTAX_CHECKED` | PASS | Generator `compile()` checked all 12 generated Python files; `compileall` also exited 0. |
| `IMPORT_CHECKED` | PASS | Generator imported all 10 `src` modules and loaded `tests.py`. |
| `BUILD VERIFIED` | PASS | `python3 -m compileall -q .` exited 0 from `dpco-algebra-poc/`; generation also passed syntax and import checks. |
| `EXECUTED` | PASS | `python3 tests.py` ran to completion. |
| `TESTS PASSED` | PASS | 19 PASS, 0 FAIL: T01–T10 matrix 11/11, seven supplemental checks, and one ledger check. |

These are observed results from commands run in this environment, not claims
about a separate Linux Mint installation.

## Test output

```text
[PASS] T01 - Exact Arithmetic
[PASS] T02 - False Claim
[PASS] T03.1 - Shift Contradiction
[PASS] T03.2 - Proportional Contradiction
[PASS] T04 - Capability Gap
[PASS] T05 - Verification Failure
[PASS] T06 - Deterministic Dispatch
[PASS] T07 - Forced Executor Constraint Violation
[PASS] T08 - Consistent Two-Equation System
[PASS] T09 - Consistent Three-Equation System
[PASS] T10 - Three-Equation Contradiction
[PASS] E01 - Negative Coefficients
[PASS] E02 - Fractional Coefficients
[PASS] E03 - Large Integer Coefficients
[PASS] E04 - Missing Parameter
[PASS] E05 - Zero Coefficient
[PASS] E06 - Malformed Equation
[PASS] E07 - Non-Finite Coefficient
[PASS] JSONL ledger records parse and contain required fields

SUMMARY: 19 PASS, 0 FAIL (T01-T10 matrix: 11/11;
7 supplemental checks plus ledger validation)
```

The generated `execution_ledger.jsonl` contains 18 task records from the
successful run. The total of 19 passing checks includes the separate ledger
validation check, which does not create an additional task record. The first
and last records were inspected; every line was also parsed with a strict JSON
parser by the test runner.

## Commands executed

Successful commands:

```sh
python3 --version
python3 -m py_compile generate_and_run.py
python3 generate_and_run.py
cd dpco-algebra-poc
python3 -m compileall -q .
python3 tests.py
cat execution_ledger.jsonl
```

During validation, one first test invocation was made from the workspace parent
instead of `dpco-algebra-poc/`, so Python could not find `tests.py`; it was
rerun from the project directory. The first T06 assertion also compared a
numerical decimal to an exact rational string; that test was corrected to use
a numeric tolerance and the full suite was rerun. The earlier diagnostic
ledger from before strict JSON serialization was removed before release freeze;
the checked-in release directory contains only the ledger from the final
successful run.
