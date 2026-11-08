# DEAS-1 Security & Artifacts Contract (v0.3.0)

## 1. Isolation Authority
**An external adapter or executor is never trusted to declare its own isolation level.**
- The DPCO Runtime Environment evaluates hosting boundaries, container cgroups, or subprocess constraints.
- If an executor requests an isolation tier unsupported by the runtime, DPCO Core rejects the admission grant.

## 2. Artifact Security & SSRF/Path Traversal Defense
1. **Allowed URI Schemes:** Only `data://`, sandbox-restricted `file://`, and `cas://` (Content-Addressed Storage) are permitted. Remote `http://` and `https://` URIs are blocked by default to prevent SSRF.
2. **Path Traversal & Boundary Defense:** All file URIs are resolved to canonical paths (`fs.realpathSync`) and validated against the sandbox root using strict path-prefix boundary checks. Security enforcement includes symlink resolution validation to prevent access outside the sandbox and TOCTOU (Time-of-Check to Time-of-Use) mitigation strategies for file access operations.
3. **Content Hash Verification:** Every artifact must include a SHA-256 `content_hash`. DPCO Core verifies hashes upon receipt; mismatches trigger `ARTIFACT_TRANSFER_FAILED`.
4. **Serialization Safety:** Arbitrary code execution formats (such as Python `pickle`) are strictly prohibited. All communication uses strict JSON schemas.
