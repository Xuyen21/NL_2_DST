from evaluations.verification import VerifyOutput
from verification import VerificationResult
from verification.stats import ActivitiesStats


class VerifyActivities(VerifyOutput):
    """Verifier for activities comparing against an expected output"""

    def verify(self) -> VerificationResult[ActivitiesStats]:
        # TODO: implement
        return VerificationResult(0, 0, ActivitiesStats(), ActivitiesStats())
