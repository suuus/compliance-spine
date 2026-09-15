"""ZAVA metrics. The positive class is a *violation* the gate should ``block``.

- ``recall`` — of the seeded violations, how many did the spine actually stop? (miss = FN)
- ``false_positive_rate`` — of the clean changes, how many did it wrongly block? (FP)

Recall is the headline safety metric; the false-positive rate is what keeps the gate from
being ignored. ZAVA passes only when recall is high enough and the FP rate low enough.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Confusion:
    tp: int = 0  # violation, blocked
    fn: int = 0  # violation, missed
    fp: int = 0  # clean, wrongly blocked
    tn: int = 0  # clean, allowed

    def add(self, expected: str, predicted: str) -> None:
        if expected == "block":
            if predicted == "block":
                self.tp += 1
            else:
                self.fn += 1
        else:
            if predicted == "allow":
                self.tn += 1
            else:
                self.fp += 1

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 1.0

    @property
    def false_positive_rate(self) -> float:
        denom = self.fp + self.tn
        return self.fp / denom if denom else 0.0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 1.0

    @property
    def accuracy(self) -> float:
        denom = self.tp + self.fn + self.fp + self.tn
        return (self.tp + self.tn) / denom if denom else 1.0
