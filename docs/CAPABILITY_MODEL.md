# DPCO Capability & Qualification Model

## 1. Overview
DPCO evaluates trust per **Capability** and per **Execution Result**, never granting blanket trust to an entire software suite.

## 2. Capability Descriptors (CSP-0.2 Compatible)
External executors declare their capabilities using structured descriptors:
- **Identifier:** e.g., `arithmetic.linear.solve` or `geometry.2d.intersect`.
- **Input/Output Schemas:** JSON Schema validation definitions.
- **Constraints:** Determinism, exact arithmetic support, persistent session requirements, side-effect classifications (`NONE`, `READ_ONLY_IO`, `SANDBOX_IO`, `DESTRUCTIVE`).
- **Precision:** Numerical tolerances ($\varepsilon$) and significant digit bounds.

## 3. Qualification Tiers & Internal Mapping
DPCO separates high-level architectural qualification from operational runtime registry types.

### Evidence Maturity (Architectural Tiers)
- `DECLARED`: Executor passport claim.
- `INSPECTED`: Static analysis/schema audit.
- `TESTED`: Functional test matrix pass.
- `INSTANCE_VERIFIED`: Result confirmed via independent verifier.
- `DOMAIN_VERIFIED`: Formally proven or rigorously validated across domain.

### Operational Registry Mapping (`src/core/registry.ts`)
| Conceptual Tier | Runtime Enum / Type | Note |
| :--- | :--- | :--- |
| `DECLARED` | `REGISTRATION_PASSED` | Capability manifest valid. |
| `TESTED` | `TEST_SUITE_PASSED` | Functional matrix pass. |
| `INSTANCE_VERIFIED` | `VERIFIED` | Specific output audit success. |
| `DOMAIN_VERIFIED` | `N/A` | Conceptual only; no runtime enum equivalence. |

*Crucial Distinction:* `INSTANCE_VERIFIED` provides high confidence for a specific task output via independent verifier back-substitution, but it does **not** promote the executor to `DOMAIN_VERIFIED` status for all possible future inputs. Each capability must be qualified separately.


## 4. Admission Control & R-Levels
- **Fail-Closed Default:** Unvetted executors default to `UNCLASSIFIED` role and are blocked from production dispatch.
- **Roles:** `PRODUCTION`, `NEGATIVE_CONTROL`, `BENCHMARK_ORACLE`, `UNCLASSIFIED`.
- **Risk Levels ($R0$–$R4$):** Mapped to task execution modes and approval gates.
