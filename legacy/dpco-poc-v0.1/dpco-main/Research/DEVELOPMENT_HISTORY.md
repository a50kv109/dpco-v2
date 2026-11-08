# DPCO — Development History and Research Notes

## Provenance

This note was prepared by the VS Code Agent during project consolidation from
the current workspace and the conversation history. It is not an original
Gemini or ChatGPT deliverable. Original Gemini files that were available on
disk are copied verbatim under `Original-Materials/Gemini/`.

## Recorded milestones

1. Gemini supplied a DPCO PoC generator and Iteration 02 audit. Its source is
   preserved as `Original-Materials/Gemini/python.md` and
   `Original-Materials/Gemini/code_artifact.md`.
2. A review in the conversation identified nested newline escaping and
   questioned the claimed generated-source syntax check. The corresponding
   launch instructions are preserved as
   `Original-Materials/Gemini/gemini-code-1794000105350.sh`.
3. The current VS Code Agent inspected those materials, generated a standalone
   PoC, added validation/build/import checks, and executed its tests in the
   available Linux environment.
4. Validation exposed a T06 test expectation mismatch: a float result was
   being compared as an exact rational string. The test was corrected to use a
   numeric tolerance and the full test suite passed.
5. An additional strict-JSON review identified that Python's default JSON
   serializer accepts non-standard `Infinity` tokens. The ledger now serializes
   non-finite numeric input as text and rejects non-standard JSON constants in
   its test.
6. The release report records **19 PASS / 0 FAIL**: 11 primary matrix checks,
   seven supplemental input cases, and one ledger validation.

## Recorded review findings

- The generator and its generated source involve two distinct newline escaping
  levels.
- Syntax checks must cover generated files and imports, not just the generator.
- Unified compatibility must protect both ordinary dispatch and
  `force_executor`.
- Input structure and numerical finiteness must be checked before domain
  logic.
- A consistent system being admitted by a contradiction check is not the same
  as solving that system; without a solver the result must remain
  `CAPABILITY_GAP`.
- The existing PoC has no `solve_system` executor.

## Scope note

Conversation messages and older drafts that were not present as files at
consolidation time are not reproduced here as original documents. No
unavailable materials are represented as recovered source artifacts.
