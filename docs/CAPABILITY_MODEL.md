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
DPCO recognizes two levels of qualification terminology:
1. **Evidence Registry / Architectural Tiers (`docs/CAPABILITY_MODEL.md`):** `DECLARED`, `INSPECTED`, `TESTED`, `INSTANCE_VERIFIED`, `DOMAIN_VERIFIED`.
2. **Core Registry Types (`src/core/registry.ts`):** Internal runtime validation handles baseline capability registration and state checks. 

*Mapping Note:* An `INSTANCE_VERIFIED` result confirms a specific execution output via independent verifier back-substitution, but does not grant blanket `DOMAIN_VERIFIED` status for all possible inputs across the domain.

## 4. Admission Control & R-Levels
- **Fail-Closed Default:** Unvetted executors default to `UNCLASSIFIED` role and are blocked from production dispatch.
- **Roles:** `PRODUCTION`, `NEGATIVE_CONTROL`, `BENCHMARK_ORACLE`, `UNCLASSIFIED`.
- **Risk Levels ($R0$–$R4$):** Mapped to task execution modes and approval gates.
