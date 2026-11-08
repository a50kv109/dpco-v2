# DPCO Capability & Qualification Model

## 1. Overview
DPCO evaluates trust per **Capability** and per **Execution Result**, never granting blanket trust to an entire software suite.

## 2. Capability Descriptors (CSP-0.2 Compatible)
External executors declare their capabilities using structured descriptors:
- **Identifier:** e.g., `arithmetic.linear.solve` or `geometry.2d.intersect`.
- **Input/Output Schemas:** JSON Schema validation definitions.
- **Constraints:** Determinism, exact arithmetic support, persistent session requirements, side-effect classifications (`NONE`, `READ_ONLY_IO`, `SANDBOX_IO`, `DESTRUCTIVE`).
- **Precision:** Numerical tolerances ($\varepsilon$) and significant digit bounds.

## 3. Qualification Tiers (Orthogonal Evidence Dimensions)
1. **DECLARED:** Claimed in executor passport.
2. **INSPECTED:** Static schema and interface audit.
3. **TESTED:** Passed functional test matrix.
4. **INSTANCE_VERIFIED:** Specific result independently checked by verifier.
5. **DOMAIN_VERIFIED:** Formally proven or rigorously validated across domain.

## 4. Admission Control & R-Levels
- **Fail-Closed Default:** Unvetted executors default to `UNCLASSIFIED` role and are blocked from production dispatch.
- **Roles:** `PRODUCTION`, `NEGATIVE_CONTROL`, `BENCHMARK_ORACLE`, `UNCLASSIFIED`.
- **Risk Levels ($R0$–$R4$):** Mapped to task execution modes and approval gates.
