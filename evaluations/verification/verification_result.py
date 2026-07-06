from dataclasses import dataclass
from typing import TypeVar, Generic

from verification import Stats


TStats = TypeVar("TStats", bound=Stats)


@dataclass
class VerificationResult(Generic[TStats]):
    total_fields: int
    correct_fields: int
    missing_fields: TStats
    hallu_fields: TStats

