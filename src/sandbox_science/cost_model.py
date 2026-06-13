from __future__ import annotations

import numpy as np
from pydantic import BaseModel


class ExecutionSpec(BaseModel):
    """Describes what to execute and its resource envelope."""

    command: str = "python"
    args: list[str] = []
    timeout_seconds: float = 300.0
    memory_limit_mb: int = 1024
    working_dir: str | None = None
    env: dict[str, str] = {}


class CostEstimate(BaseModel):
    """Predicted resource consumption for a proposed execution."""

    cpu_seconds: float
    memory_mb: float
    wall_seconds: float
    total_cost: float
    confidence: float


class CostActual(BaseModel):
    """Observed resource consumption after execution."""

    cpu_seconds: float
    memory_mb: float
    wall_seconds: float
    total_cost: float


class CostEstimator:
    """Learned cost predictor using linear regression over feature vectors.

    Starts with a conservative default rate and refines predictions as
    actual observations arrive via :meth:`update`.
    """

    def __init__(self, default_rate: float = 0.001) -> None:
        self._default_rate = default_rate
        self._X: list[list[float]] = []
        self._y: list[float] = []
        self._weights: np.ndarray | None = None
        self._n_observations: int = 0

    def estimate(self, spec: ExecutionSpec) -> CostEstimate:
        estimated_wall = spec.timeout_seconds * 0.5
        estimated_cpu = estimated_wall * 0.8
        estimated_mem = float(spec.memory_limit_mb)

        if self._weights is not None:
            features = np.array([estimated_cpu, estimated_mem, estimated_wall])
            total_cost = max(float(np.dot(features, self._weights)), 0.0)
            confidence = min(self._n_observations / 10.0, 1.0)
        else:
            total_cost = (
                estimated_wall * self._default_rate
                + estimated_mem * self._default_rate * 0.001
            )
            confidence = 0.1

        return CostEstimate(
            cpu_seconds=estimated_cpu,
            memory_mb=estimated_mem,
            wall_seconds=estimated_wall,
            total_cost=total_cost,
            confidence=confidence,
        )

    def update(self, actual: CostActual) -> None:
        features = [actual.cpu_seconds, actual.memory_mb, actual.wall_seconds]
        self._X.append(features)
        self._y.append(actual.total_cost)
        self._n_observations += 1

        if self._n_observations >= 3:
            X_arr = np.array(self._X)
            y_arr = np.array(self._y)
            self._weights = np.linalg.lstsq(X_arr, y_arr, rcond=None)[0]
