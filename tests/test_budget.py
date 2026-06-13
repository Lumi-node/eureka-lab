"""Tests for budget-aware sandbox execution."""

from sandbox_science.cost_model import CostActual, CostEstimator, ExecutionSpec
from sandbox_science.sandbox import ExperimentRequest, Sandbox


def test_within_budget_succeeds(tmp_path):
    sandbox = Sandbox(workspace=tmp_path / "ws")
    req = ExperimentRequest(
        code="print('hello')",
        budget=10.0,
        timeout_seconds=5,
        memory_limit_mb=256,
    )
    result = sandbox.submit(req)
    assert result.success
    assert "hello" in result.run_log.stdout
    assert result.cost_actual is not None
    assert result.cost_actual.total_cost <= req.budget


def test_over_budget_rejected(tmp_path):
    sandbox = Sandbox(workspace=tmp_path / "ws")
    req = ExperimentRequest(
        code="print('hello')",
        budget=0.0001,
        timeout_seconds=60,
        memory_limit_mb=512,
    )
    result = sandbox.submit(req)
    assert not result.success
    assert result.rejected
    assert "budget" in result.rejection_reason.lower()


def test_cost_estimator_learns():
    estimator = CostEstimator()
    spec = ExecutionSpec(command="python", timeout_seconds=10, memory_limit_mb=256)

    est1 = estimator.estimate(spec)
    assert est1.confidence < 0.5

    for _ in range(5):
        estimator.update(
            CostActual(
                cpu_seconds=2.0, memory_mb=100.0, wall_seconds=3.0, total_cost=0.5,
            )
        )

    est2 = estimator.estimate(spec)
    assert est2.confidence > est1.confidence
    assert est2.total_cost != est1.total_cost


def test_timeout_enforcement(tmp_path):
    sandbox = Sandbox(workspace=tmp_path / "ws")
    req = ExperimentRequest(
        code="import time; time.sleep(100)",
        budget=100.0,
        timeout_seconds=2,
        memory_limit_mb=256,
    )
    result = sandbox.submit(req)
    assert result.run_log.timed_out
    assert result.run_log.wall_seconds < 10


def test_actual_cost_tracked(tmp_path):
    sandbox = Sandbox(workspace=tmp_path / "ws")
    req = ExperimentRequest(
        code="print(sum(range(1000)))",
        budget=10.0,
        timeout_seconds=5,
        memory_limit_mb=256,
    )
    result = sandbox.submit(req)
    assert result.success
    assert result.cost_actual is not None
    assert result.cost_actual.wall_seconds > 0
    assert result.cost_actual.total_cost > 0
