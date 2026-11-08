from .models import ClaimVerdict, ExecStatus, VerifyStatus


class ResultClassifier:
    def classify(
        self,
        exec_status: ExecStatus,
        verify_status: VerifyStatus,
        claim_verdict: ClaimVerdict,
    ) -> tuple[ExecStatus, ClaimVerdict, VerifyStatus]:
        if exec_status == ExecStatus.BLOCKED:
            return exec_status, ClaimVerdict.UNKNOWN, VerifyStatus.UNVERIFIED
        if exec_status == ExecStatus.FAILED:
            return exec_status, ClaimVerdict.UNKNOWN, VerifyStatus.NOT_APPLICABLE
        return exec_status, claim_verdict, verify_status
