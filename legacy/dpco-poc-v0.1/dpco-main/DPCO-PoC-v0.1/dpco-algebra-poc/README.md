# DPCO Algebra PoC v0.1

Release frozen: 2026-11-06.

This standalone Python PoC demonstrates deterministic routing and verification
for equations in the supported form `a*x + b = c`.

## Project layout

- `src/`: DPCO core, capability registry, dispatcher, executors, validation,
  contradiction gate, verifier, classifier, and JSONL ledger.
- `tests.py`: the T01–T10 matrix (11 checks) plus seven supplemental boundary
  checks and a strict JSONL validation.
- `execution_ledger.jsonl`: records produced by the most recent test run.
- `../generate_and_run.py`: reproducibly generates the Python sources, compiles
  every generated `.py` file, and checks imports.

The generator is the canonical source for generated Python files. Running it
again rewrites those generated files; the audit, reports, README, and ledger are
not generated.

## Run

From the workspace root:

```sh
python3 --version
python3 -m py_compile generate_and_run.py
python3 generate_and_run.py
```

Then run the build and tests from this directory:

```sh
cd dpco-algebra-poc
python3 -m compileall -q .
python3 tests.py
cat execution_ledger.jsonl
```

The test runner exits nonzero if any check fails. Test runs append records to the
ledger. Non-finite numeric values are represented as strings so every line
remains standards-compliant JSON.

## Status semantics

- `ExecStatus` describes whether processing succeeded, failed, or was blocked.
- `VerifyStatus` describes whether the computed root was checked.
- `ClaimVerdict` describes the user's claim separately from execution and
  verification.

An executor can return a result successfully even when the verifier rejects
that result; this is intentional (`SUCCESS / UNKNOWN / UNVERIFIED`).

## Scope and limitations

The PoC does not solve systems of equations. The contradiction gate can detect
inconsistent pairs in a system, but consistent systems receive `CAPABILITY_GAP`
because no system solver is registered. Exact execution and exact verification
both use Python's `fractions.Fraction`; they are algorithmically separate but
not independent of the same arithmetic library. The numerical verifier uses
finite-value checks and tolerances, not a proof of arbitrary-precision
correctness.

See [RELEASE_NOTES.md](RELEASE_NOTES.md),
[ENGINEERING_AUDIT.md](ENGINEERING_AUDIT.md), and
[EXECUTION_REPORT.md](EXECUTION_REPORT.md) for implementation findings and
observed validation results.
