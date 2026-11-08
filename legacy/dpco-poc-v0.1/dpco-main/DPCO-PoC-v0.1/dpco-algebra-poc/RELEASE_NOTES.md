# DPCO PoC v0.1 — Release Notes

**Release date:** 2026-11-06
**Status:** Frozen proof-of-concept release

## Included

- Deterministic capability-based dispatch with a shared compatibility check
  for ordinary and forced executor selection.
- Exact rational and numerical executors for scalar equations of the form
  `a*x + b = c`.
- Independent root verification and separate user-claim verdicts.
- Pairwise contradiction detection for supported linear equation systems.
- Input validation for missing, malformed, zero, and non-finite coefficients.
- Three distinct status dimensions: execution, verification, and claim verdict.
- JSONL execution ledger with strict JSON serialization.
- Generator checks for syntax of all generated Python files and imports.
- Test coverage: T01–T10 (11 checks), seven additional boundary cases, and a
  ledger validation; final observed result **19 PASS / 0 FAIL**.

## Known limitations

- Systems of equations are not solved. Consistent systems are admitted by the
  contradiction gate and then return `CAPABILITY_GAP`.
- The supported contradiction model is limited to pairs in `a*x + b = c`.
- Exact executor and verifier share Python's `Fraction` arithmetic library.
- Numerical verification uses tolerances and is not an arbitrary-precision
  proof.
- The test-only bad executor can still be selected through the explicit
  `force_executor` interface; production use should restrict that override.
- The JSONL ledger has no inter-process locking or tamper-evidence.

## Reproducibility

Run from the workspace root:

```sh
python3 --version
python3 -m py_compile generate_and_run.py
python3 generate_and_run.py
cd dpco-algebra-poc
python3 -m compileall -q .
python3 tests.py
cat execution_ledger.jsonl
```

The recorded 19/0 result was executed in the current VS Code Linux environment
with Python 3.12.3. It does not assert that the project was executed on a
separate Linux Mint installation.

See [ENGINEERING_AUDIT.md](ENGINEERING_AUDIT.md) for the architecture and
review findings, and [EXECUTION_REPORT.md](EXECUTION_REPORT.md) for observed
commands and test output.
