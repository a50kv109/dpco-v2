# DPCO PoC v0.1 — Engineering Audit

## Inventory and provenance

The active workspace is a TypeScript Geometry Reasoning Core; it contained no
DPCO files or Python sources at takeover. The supplied materials were:

- `python.md` — the 419-line Gemini generator, marked Corrective Iteration 02.
- `code_artifact.md` — the matching Iteration 02 audit.
- `gemini-code-1794000105350.sh` — two Python launch commands.
- `-ai-geometry-skill-2-main.zip` — its file listing contained no DPCO,
  `generate_and_run.py`, `ENGINEERING_AUDIT.md`, or `tests.py`.

No competing DPCO source versions were present in the workspace. The supplied
files were left unchanged. The DPCO implementation was placed in the separate
`dpco-algebra-poc/` directory; the generator is
[`../generate_and_run.py`](../generate_and_run.py). The existing Geometry
Reasoning Core files were not modified.

## Architecture

The PoC keeps the requested roles and status dimensions:

- `DPCOCore` performs validation, contradiction checks, compatible dispatch,
  execution, verification, classification, and ledger recording.
- `CapabilityRegistry.is_compatible()` is the shared compatibility check for
  candidate discovery and `force_executor`.
- `DeterministicDispatcher` sorts compatible production executors by cost and
  ID. Executors marked `is_test` are not normal dispatch candidates.
- `ExactExecutor` uses `Fraction`; `NumericalExecutor` uses finite floats.
- `IndependentVerifier` independently evaluates the returned root and then
  evaluates the user's claim.
- `ContradictionGate` checks every equation pair for the supported
  `a*x + b = c` representation.
- `ExecutionLedger` records JSON Lines with input, executor/result when
  available, reason, timestamp, and all three final statuses.

The independent dimensions remain `ExecStatus`, `ClaimVerdict`, and
`VerifyStatus`; a claim is not inferred from execution success.

## Defects corrected

1. **Nested newline escaping.** The generator templates are raw strings, so
   `src/ledger.py` retains the source expression
   `json.dumps(...) + "\n"`. File generation appends an actual newline with
   `content.strip() + "\n"`.
2. **No generated-source gate.** The generator compiles every generated
   `*.py`, reports failing path/line/message, then imports each source module
   and `tests.py`. A failure returns a nonzero exit status and suppresses the
   ready message.
3. **Input structure and coefficient validation.** Missing keys, malformed
   equation objects, empty systems, booleans, non-numeric/non-finite values,
   and zero `a` are blocked with explicit validation reasons.
4. **Exact contradiction comparisons.** Pairwise consistency checks use
   `Fraction`, avoiding float-equality artifacts for supported rational data.
5. **Test-only executor routing.** `test_bad_solver` remains available for
   explicit verification-failure tests but is excluded from automatic dispatch.
   Forced executor selection still passes through unified compatibility checks.
6. **Status classification.** A blocked task is `UNVERIFIED`; a failed
   execution has `NOT_APPLICABLE` verification; a successful execution retains
   the verifier's actual result.
7. **Ledger completeness and strict JSON.** The ledger now includes the claim
   and constraints. Non-finite input floats are rendered as strings and JSON
   serialization disallows non-standard `NaN`/`Infinity` tokens.
8. **Numerical dispatch test expectation.** T06 checks a numerical result with
   tolerance rather than comparing its decimal representation to an exact
   rational string.

## Verification matrix

| Checks | Coverage | Observed |
|---|---|---|
| T01–T10 (11 checks) | Exact result, false claim, two contradiction forms, capability gap, bad executor verification, deterministic dispatch, force constraint, consistent 2/3-equation systems, 3-equation contradiction | 11 PASS |
| E01–E07 (7 checks) | Negative coefficients, fractional coefficients, large integers, missing coefficient, zero coefficient, malformed system equation, non-finite coefficient | 7 PASS |
| Ledger check | Strict JSON parsing and required fields | 1 PASS |
| **Total** | **19 checks** | **19 PASS, 0 FAIL** |

T08 and T09 are not solved: the gate admits consistent systems and the
dispatcher correctly returns `CAPABILITY_GAP`. T10 is blocked by a conflicting
pair.

## Remaining limitations

- The domain is restricted to scalar linear equations in `a*x + b = c`.
- The gate detects pairwise contradictions, but no `solve_system` executor is
  registered.
- Exact execution and exact verification both use Python `Fraction`; this
  leaves a shared-library common-mode risk.
- Numerical verification relies on `rel_tol=1e-5` and `abs_tol=1e-9`.
- The test executor is hidden from normal dispatch, but the explicit
  `force_executor` interface can select it. That override should be restricted
  or removed before production use.
- The ledger is append-only at the application level but has no inter-process
  locking or tamper-evidence.

No broader architecture changes are proposed in this iteration.
