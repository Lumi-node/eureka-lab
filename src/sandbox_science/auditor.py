from __future__ import annotations

from enum import Enum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class AuditFlag(str, Enum):
    CONSTANT_OUTPUT = "constant_output"
    DUPLICATE_HASH = "duplicate_hash"
    PERFECT_SCORE = "perfect_score"
    OUTPUT_MANIPULATION = "output_manipulation"
    METRIC_INFLATION = "metric_inflation"


class AuditReport(BaseModel):
    """Result of auditing a single experiment result."""

    passed: bool
    flags: list[AuditFlag] = []
    details: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class CrossValReport(BaseModel):
    """Result of cross-validating multiple experiment results."""

    consistent: bool
    outlier_run_ids: list[str] = []
    flags: list[AuditFlag] = []
    variance: float = 0.0
    details: dict[str, Any] = Field(default_factory=dict)


class _ResultLike:
    """Structural type for ExperimentResult (avoids circular import)."""

    run_id: str
    success: bool
    output_hash: str
    metrics: dict[str, float]


class Auditor:
    """Independent meta-evaluator that detects reward-hacking patterns."""

    PERFECT_VALUES = frozenset({0.0, 1.0})
    PERFECT_THRESHOLD = 2

    def verify(self, result: _ResultLike) -> AuditReport:
        flags: list[AuditFlag] = []
        details: dict[str, Any] = {}

        if result.metrics:
            perfect_keys = [
                k for k, v in result.metrics.items() if v in self.PERFECT_VALUES
            ]
            if len(perfect_keys) >= self.PERFECT_THRESHOLD:
                flags.append(AuditFlag.PERFECT_SCORE)
                details["perfect_metrics"] = perfect_keys

        return AuditReport(
            passed=len(flags) == 0,
            flags=flags,
            details=details,
        )

    def cross_validate(self, results: list[_ResultLike]) -> CrossValReport:
        flags: list[AuditFlag] = []
        details: dict[str, Any] = {}

        hashes = [r.output_hash for r in results if r.output_hash]
        if hashes:
            unique = set(hashes)
            if len(unique) == 1 and len(hashes) > 1:
                flags.append(AuditFlag.CONSTANT_OUTPUT)
            elif len(unique) < len(hashes):
                flags.append(AuditFlag.DUPLICATE_HASH)

        outlier_ids, variance = self._find_outliers(results)

        consistent = len(flags) == 0 and len(outlier_ids) == 0
        return CrossValReport(
            consistent=consistent,
            outlier_run_ids=outlier_ids,
            flags=flags,
            variance=variance,
            details=details,
        )

    def _find_outliers(
        self, results: list[_ResultLike]
    ) -> tuple[list[str], float]:
        if not results:
            return [], 0.0

        all_metrics: set[str] = set()
        for r in results:
            all_metrics.update(r.metrics.keys())

        if not all_metrics:
            return [], 0.0

        outlier_ids: set[str] = set()
        total_variance = 0.0

        for metric_name in all_metrics:
            values: list[float] = []
            run_ids: list[str] = []
            for r in results:
                if metric_name in r.metrics:
                    values.append(r.metrics[metric_name])
                    run_ids.append(r.run_id)

            if len(values) < 3:
                continue

            arr = np.array(values)
            total_variance += float(np.var(arr))

            q1 = float(np.percentile(arr, 25))
            q3 = float(np.percentile(arr, 75))
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr

            for i, v in enumerate(values):
                if v < lower or v > upper:
                    outlier_ids.add(run_ids[i])

        return sorted(outlier_ids), total_variance
