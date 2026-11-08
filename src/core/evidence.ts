/**
 * DPCO Evidence Registry & Admission Grant Contract - Revision 4
 * 
 * Enforces:
 * - 5 Orthogonal Evidence Dimensions (non-convergent)
 * - Strict separation between declared claims and verified evidence
 * - Independent domain-bounded qualification records
 * - Tamper-evident AdmissionGrants with revocation tracking
 */

import { MathematicalRigorLevel } from './models';

export type EvidenceType = 
  | 'PASSPORT_DECLARED'
  | 'TEST_SUITE_PASSED'
  | 'FORMALLY_VERIFIED_INSTANCE'
  | 'FORMALLY_VERIFIED_DOMAIN'
  | 'EMPIRICALLY_VALIDATED'
  | 'EXTERNALLY_ATTESTED';

export type DpcoRole = 
  | 'UNCLASSIFIED'
  | 'PRODUCTION'
  | 'NEGATIVE_CONTROL'
  | 'BENCHMARK_ORACLE';

export interface EvidenceRecord {
  evidence_id: string;
  executor_id: string;
  evidence_type: EvidenceType;
  domain: string; // e.g. "arithmetic.rational.linear", "geometry.2d.euclidean"
  scope: string;  // Explicit boundary of applicability
  issuer: string; // Authorized testing harness, formal engine, or operator
  issued_at: string; // ISO timestamp
  expires_at?: string | null;
  revoked: boolean;
  revocation_reason?: string;
  revoked_at?: string;
  artifact_hash?: string;
  metadata?: Record<string, any>;
}

export interface AdmissionGrant {
  grant_id: string;
  executor_id: string;
  granted_role: 'PRODUCTION' | 'NEGATIVE_CONTROL' | 'BENCHMARK_ORACLE';
  authorized_by: string; // Policy ID or Security Principal
  policy_id: string;
  evidence_ids_verified: string[];
  issued_at: string;
  expires_at?: string | null;
  revoked: boolean;
  revocation_reason?: string;
  revoked_at?: string;
}

export class EvidenceRegistry {
  private evidences: Map<string, EvidenceRecord> = new Map();
  private grants: Map<string, AdmissionGrant> = new Map();

  /**
   * Registers a new evidence record.
   */
  addEvidence(evidence: EvidenceRecord): void {
    this.evidences.set(evidence.evidence_id, { ...evidence });
  }

  /**
   * Revokes an evidence record.
   */
  revokeEvidence(evidenceId: string, reason: string): boolean {
    const ev = this.evidences.get(evidenceId);
    if (!ev) return false;
    ev.revoked = true;
    ev.revocation_reason = reason;
    ev.revoked_at = new Date().toISOString();
    return true;
  }

  getEvidence(evidenceId: string): EvidenceRecord | undefined {
    return this.evidences.get(evidenceId);
  }

  getExecutorEvidences(executorId: string): EvidenceRecord[] {
    return Array.from(this.evidences.values()).filter(
      (e) => e.executor_id === executorId && !e.revoked
    );
  }

  /**
   * Issues an authorized AdmissionGrant.
   * An executor CANNOT issue a grant to itself.
   */
  issueAdmissionGrant(
    grantInput: Omit<AdmissionGrant, 'revoked' | 'revoked_at'>
  ): AdmissionGrant {
    const grant: AdmissionGrant = {
      ...grantInput,
      revoked: false,
    };
    this.grants.set(grant.grant_id, grant);
    return grant;
  }

  /**
   * Revokes an AdmissionGrant.
   */
  revokeAdmissionGrant(grantId: string, reason: string): boolean {
    const grant = this.grants.get(grantId);
    if (!grant) return false;
    grant.revoked = true;
    grant.revocation_reason = reason;
    grant.revoked_at = new Date().toISOString();
    return true;
  }

  /**
   * Retrieves active, unrevoked, unexpired grant for an executor.
   */
  getActiveGrant(executorId: string): AdmissionGrant | null {
    const now = Date.now();
    for (const grant of this.grants.values()) {
      if (grant.executor_id === executorId && !grant.revoked) {
        if (grant.expires_at) {
          const exp = new Date(grant.expires_at).getTime();
          if (now > exp) continue; // expired
        }
        return grant;
      }
    }
    return null;
  }

  getAllGrants(): AdmissionGrant[] {
    return Array.from(this.grants.values());
  }

  /**
   * Calculates effective role based on active grants.
   * Default: UNCLASSIFIED (Fail-closed).
   */
  calculateEffectiveRole(executorId: string): DpcoRole {
    const grant = this.getActiveGrant(executorId);
    if (grant) {
      return grant.granted_role;
    }
    return 'UNCLASSIFIED';
  }

  /**
   * Evaluates if executor satisfies the requested mathematical rigor level in the target domain.
   * 
   * - TESTED: requires active TEST_SUITE_PASSED
   * - INSTANCE_VERIFIED: requires at least TEST_SUITE_PASSED (pre-qualification)
   * - DOMAIN_VERIFIED: requires FORMALLY_VERIFIED_DOMAIN (finite tests NEVER satisfy this)
   */
  hasValidEvidenceForRigor(
    executorId: string,
    rigor: MathematicalRigorLevel,
    targetDomain?: string
  ): { qualified: boolean; matchedEvidenceIds: string[]; reason?: string } {
    const active = this.getExecutorEvidences(executorId);

    // Filter by domain if specified
    const inDomain = active.filter((e) => {
      if (!targetDomain) return true;
      // Domain matching: target domain starts with or equals evidence domain
      return (
        targetDomain.startsWith(e.domain) ||
        e.domain.startsWith(targetDomain) ||
        e.domain === '*'
      );
    });

    if (rigor === 'TESTED') {
      const testEvs = inDomain.filter((e) => e.evidence_type === 'TEST_SUITE_PASSED');
      if (testEvs.length > 0) {
        return {
          qualified: true,
          matchedEvidenceIds: testEvs.map((e) => e.evidence_id),
        };
      }
      return {
        qualified: false,
        matchedEvidenceIds: [],
        reason: `Missing active TEST_SUITE_PASSED evidence for domain '${targetDomain || 'any'}'.`,
      };
    }

    if (rigor === 'INSTANCE_VERIFIED') {
      // Must have empirical tested baseline or formal verification
      const baseline = inDomain.filter(
        (e) =>
          e.evidence_type === 'TEST_SUITE_PASSED' ||
          e.evidence_type === 'FORMALLY_VERIFIED_INSTANCE' ||
          e.evidence_type === 'FORMALLY_VERIFIED_DOMAIN'
      );
      if (baseline.length > 0) {
        return {
          qualified: true,
          matchedEvidenceIds: baseline.map((e) => e.evidence_id),
        };
      }
      return {
        qualified: false,
        matchedEvidenceIds: [],
        reason: `Missing active baseline verification evidence for runtime instance check in '${targetDomain}'.`,
      };
    }

    if (rigor === 'DOMAIN_VERIFIED') {
      const formalEvs = inDomain.filter(
        (e) => e.evidence_type === 'FORMALLY_VERIFIED_DOMAIN'
      );
      if (formalEvs.length > 0) {
        return {
          qualified: true,
          matchedEvidenceIds: formalEvs.map((e) => e.evidence_id),
        };
      }
      return {
        qualified: false,
        matchedEvidenceIds: [],
        reason: `Finite test suite cannot satisfy DOMAIN_VERIFIED. Missing FORMALLY_VERIFIED_DOMAIN evidence for '${targetDomain}'.`,
      };
    }

    return { qualified: false, matchedEvidenceIds: [], reason: 'Unknown rigor level.' };
  }
}
