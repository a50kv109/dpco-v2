import { DPCOCore } from '../src/core/dpcoCore';
import { runFullVerificationSuite } from '../src/core/testSuite';
import { runCspTestSuite } from '../src/core/cspTestSuite';
import { runRevision4TestSuite } from '../src/core/revision4TestSuite';

console.log('================================================================');
console.log('    DPCO TRIPLE TEST RUNNER: CORE (19) + CSP (10) + R4 (20)     ');
console.log('================================================================\n');

const core = new DPCOCore();

// 1. Run Baseline DPCO Core 19 Tests
console.log('--- 1. RUNNING DPCO CORE VERIFICATION MATRIX (19 CHECKS) ---');
const coreSuite = runFullVerificationSuite(core);
for (const r of coreSuite.results) {
  const badge = r.passed ? '[PASS]' : '[FAIL]';
  console.log(`${badge} ${r.id.padEnd(6)}: ${r.name} (${r.durationMs}ms)`);
  if (!r.passed) {
    console.error(`       Expected: ${r.expectedStatus.join('/')}, Got: ${r.actualStatus.join('/')}`);
    if (r.error) console.error(`       Error: ${r.error}`);
  }
}
console.log(`\nCORE SUMMARY: ${coreSuite.passCount} PASS / ${coreSuite.failCount} FAIL (${coreSuite.totalDurationMs}ms)\n`);

// 2. Run CSP-0.2 Validator 10 Tests
console.log('--- 2. RUNNING CSP-0.2 INTEGRATION MATRIX (10 CHECKS) ---');
const cspSuite = runCspTestSuite(core);
for (const r of cspSuite.results) {
  const badge = r.passed ? '[PASS]' : '[FAIL]';
  console.log(`${badge} ${r.id.padEnd(8)}: ${r.name} (${r.durationMs}ms)`);
  if (!r.passed) {
    console.error(`       Expected: ${r.expected}`);
    console.error(`       Actual:   ${r.actual}`);
  }
}
console.log(`\nCSP SUMMARY:  ${cspSuite.passCount} PASS / ${cspSuite.failCount} FAIL (${cspSuite.totalDurationMs}ms)\n`);

// 3. Run DPCO v0.2.0 Revision 4 Architecture Acceptance Suite (20 Checks)
console.log('--- 3. RUNNING REVISION 4 ACCEPTANCE MATRIX (20 CHECKS) ---');
const r4Suite = runRevision4TestSuite(core);
let currentGroup = '';
for (const r of r4Suite.results) {
  if (r.group !== currentGroup) {
    currentGroup = r.group;
    console.log(`\n  [${currentGroup}]`);
  }
  const badge = r.passed ? '[PASS]' : '[FAIL]';
  console.log(`  ${badge} ${r.id.padEnd(8)}: ${r.name} (${r.durationMs}ms)`);
  if (!r.passed) {
    console.error(`         Expected: ${r.expected}`);
    console.error(`         Actual:   ${r.actual}`);
  }
}
console.log(`\nR4 SUMMARY:   ${r4Suite.passCount} PASS / ${r4Suite.failCount} FAIL (${r4Suite.totalDurationMs}ms)\n`);

console.log('================================================================');
const totalPass = coreSuite.passCount + cspSuite.passCount + r4Suite.passCount;
const totalFail = coreSuite.failCount + cspSuite.failCount + r4Suite.failCount;
console.log(`OVERALL REVISION 4 SUITE: ${totalPass} PASS / ${totalFail} FAIL`);
console.log('================================================================');

if (totalFail > 0) {
  process.exit(1);
}
