from typing import Any

from evaluations.verification import VerifyOutput


class VerifyActivities(VerifyOutput):
    """Verifier for activities comparing against an expected output"""

    def __init__(self, actual_output: list[dict], expected_output: list[dict]):
        self.actual_output = actual_output
        self.expected_output = expected_output

    def verify(self) -> dict[str, Any]:
        # TODO: implement
        return {}
