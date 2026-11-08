# DEAS-1 Runtime Contract Specification (v0.3.0)

## 1. Objectives & Asynchronous Execution Model
The DEAS-1 (DPCO External Executor Adapter Standard v1) Runtime Contract defines the standard protocol for connecting external computational engines (Python/SymPy, CLI binaries, MCP servers) to DPCO Core.

### Key Architectural Constraint:
**Synchronous and asynchronous execution paths are strictly separated.** 
- Built-in reference executors (`ExactExecutor`, `LinearSystemExecutor`) operate synchronously via `IExecutor`.
- External external adapters operate asynchronously via `IDeasExecutor.executeTask()`.
- DPCO Core provides an asynchronous execution coordinator for external tasks, preventing event loop blocking or artificial synchronous Promise unwrapping.

---

## 2. Core TypeScript Interfaces (`IDeasExecutor`)

```ts
export type DeasIsolationTier = 
  | 'IN_PROCESS_GUARDED'
  | 'WORKER_ISOLATED'
  | 'PROCESS_ISOLATED'
  | 'CONTAINER_ISOLATED';

export type DeasErrorCode =
  | 'CONNECTION_FAILED'
  | 'AUTHENTICATION_FAILED'
  | 'EXECUTION_FAILED'
  | 'TIMEOUT'
  | 'CANCELLED'
  | 'RESOURCE_LIMIT'
  | 'INVALID_INPUT'
  | 'INVALID_OUTPUT'
  | 'ARTIFACT_TRANSFER_FAILED'
  | 'PERMISSION_DENIED'
  | 'INTERNAL_ADAPTER_ERROR';

export interface CapabilityDescriptor {
  id: string;
  version: string;
  inputSchema: Record<string, any>;
  outputSchema: Record<string, any>;
  constraints: {
    deterministic: boolean;
    exactArithmetic: boolean;
    requiresPersistentSession: boolean;
    sideEffects: 'NONE' | 'READ_ONLY_IO' | 'SANDBOX_IO' | 'DESTRUCTIVE';
  };
  precision?: {
    tolerance?: number;
    maxSignificantDigits?: number;
  };
  artifactFormats: string[];
}

export interface DeasArtifactReference {
  artifact_id: string;
  producer_executor_id: string;
  execution_id: string;
  name: string;
  uri: string;
  mime_type: string;
  size_bytes: number;
  max_allowed_size_bytes: number;
  content_hash: string;
  ownership: {
    principal: string;
    permissions: 'READ_ONLY' | 'READ_WRITE';
  };
}

export interface DeasTaskRequest {
  task_id: string;
  operation: string;
  params: Record<string, any>;
  constraints?: {
    timeout_ms?: number;
    exact_arithmetic?: boolean;
    required_rigor?: string;
    max_memory_mb?: number;
  };
  artifacts_in?: DeasArtifactReference[];
  session_id?: string;
}

export interface DeasNormalizedError {
  code: DeasErrorCode;
  message: string;
  transport_error_code?: string | number;
  raw_details?: string;
  recoverable: boolean;
}

export interface DeasExecutionResponse {
  task_id: string;
  status: 'SUCCESS' | 'FAILED' | 'TIMEOUT' | 'CANCELLED' | 'BLOCKED';
  result_data?: Record<string, any>;
  artifacts_out?: DeasArtifactReference[];
  error?: DeasNormalizedError | null;
  execution_time_ms: number;
  provenance: {
    executor_id: string;
    system_id: string;
    executed_at: string;
  };
}

export interface IDeasExecutor {
  getIdentity(): { executorId: string; systemId: string; version: string; transport: string };
  discoverCapabilities(): Promise<CapabilityDescriptor[]>;
  healthCheck(): Promise<{ healthy: boolean; status: string; activeSessions?: number }>;
  executeTask(request: DeasTaskRequest): Promise<DeasExecutionResponse>;
  cancelTask?(taskId: string): Promise<boolean>;
}
```

---

## 3. Lifecycle & State Management
External executor interaction involves three distinct state models:

### 3.1 Executor States
`UNINITIALIZED` $\to$ `HEALTHY` $\iff$ `BUSY` (processing active task) $\to$ `FAULTED` $\to$ `TERMINATED`.

### 3.2 Task States
`QUEUED` $\to$ `STARTING` $\to$ `RUNNING` $\to$ (`COMPLETED` | `FAILED` | `TIMED_OUT` | `CANCELLED` | `FAULTED`).
- **Terminal States:** `COMPLETED`, `FAILED`, `TIMED_OUT`, `CANCELLED`, `FAULTED` are final states.
- **Cancellation:** `cancelTask()` may be called in `STARTING` or `RUNNING` states, transitioning Task to `CANCELLED`.

### 3.3 Session States
`SESSION_OPEN` $\to$ `SESSION_BUSY` $\to$ `SESSION_CLOSED` $\to$ `SESSION_EXPIRED`.
- Persistence of session state is managed by the external executor, and session lifecycle is independent of individual Task requests.
