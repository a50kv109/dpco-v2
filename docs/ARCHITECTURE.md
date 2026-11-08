# DPCO Architecture Specification

## 1. System Overview
DPCO (Deterministic Processing & Cognitive Orchestration) is an AI agent support middleware that coordinates deterministic mathematical and geometric computations.

## 2. Core Architectural Layers

### Layer A: Agent Interface
Receives structured JSON tasks from AI agents (ChatGPT, Gemini, etc.) and returns verified results with provenance metadata.

### Layer B: Task & Orchestration Core
- **Task Model (`src/core/models.ts`):** Standardizes operation name, parameters, and constraints.
- **Constraint Validator (`src/core/validation.ts`):** Validates parameter types, finiteness, and ranges.
- **Contradiction Gate (`src/core/contradiction.ts`):** Checks system consistency prior to dispatch.
- **Deterministic Dispatcher (`src/core/dispatcher.ts`):** Selects the optimal executor candidate based on cost and capability matching.

### Layer C: Capability & Admission
- **Capability Registry (`src/core/registry.ts`):** Maintains executor registrations and verifies requirement criteria.
- **Evidence Registry (`src/core/evidence.ts`):** Tracks orthogonal evidence dimensions and issues cryptographically backed `AdmissionGrant` objects. Fail-closed role assignment defaults to `UNCLASSIFIED`.

### Layer D: External Executor Adapters
- **Exact / Numerical / Linear Solvers (`src/core/executors.ts`):** Built-in reference execution engines.
- **Geometry Engine (`src/core/geometry.ts`):** Discrete 2D Euclidean geometry solver.
- **DEAS-1 Runtime Contract:** Asynchronous external bridge for Python/SymPy, CLI tools, and MCP servers.

### Layer E: Verification & Evidence
- **Independent Verifier (`src/core/verifier.ts`):** Autonomous mathematical cross-check subsystem.
- **Result Classifier (`src/core/classifier.ts`):** Separates execution status (`ExecStatus`), claim verdict (`ClaimVerdict`), and verification status (`VerifyStatus`).

### Layer F: Execution Ledger
- **Ledger Manager (`src/core/ledger.ts`):** Records tamper-evident SHA-256 block chains tracking every pipeline transition.
