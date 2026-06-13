from __future__ import annotations

import hashlib
import sys
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from sandbox_science.auditor import AuditReport, Auditor
from sandbox_science.cost_model import CostActual, CostEstimate, CostEstimator, ExecutionSpec
from sandbox_science.executor import Executor, RunLog
from sandbox_science.policy import PolicyEngine
from sandbox_science.provenance import CommitInfo, GitRepo


class ExperimentRequest(BaseModel):
    """What the caller submits to the sandbox."""

    run_id: str = ""
    code: str
    budget: float = 10.0
    timeout_seconds: float = 300.0
    memory_limit_mb: int = 1024
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentResult(BaseModel):
    """Full result returned from a sandbox run."""

    run_id: str
    success: bool
    run_log: RunLog | None = None
    cost_estimate: CostEstimate | None = None
    cost_actual: CostActual | None = None
    provenance: CommitInfo | None = None
    audit: AuditReport | None = None
    output_hash: str = ""
    metrics: dict[str, float] = Field(default_factory=dict)
    rejected: bool = False
    rejection_reason: str = ""


class Sandbox:
    """High-level facade: receive request, check budget, run, return result."""

    def __init__(
        self,
        workspace: Path | None = None,
        budget_limit: float = 100.0,
        auditor: Auditor | None = None,
    ) -> None:
        self._workspace = Path(workspace) if workspace else Path("sandbox_runs")
        self._workspace.mkdir(parents=True, exist_ok=True)
        self._cost_estimator = CostEstimator()
        self._policy = PolicyEngine(budget_limit=budget_limit)
        self._executor = Executor()
        self._auditor = auditor
        self._cancelled: set[str] = set()

    def submit(self, request: ExperimentRequest) -> ExperimentResult:
        run_id = request.run_id or str(uuid.uuid4())[:8]

        run_dir = self._workspace / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        code_file = run_dir / "experiment.py"
        code_file.write_text(request.code)

        spec = ExecutionSpec(
            command=sys.executable,
            args=[str(code_file)],
            timeout_seconds=request.timeout_seconds,
            memory_limit_mb=request.memory_limit_mb,
            working_dir=str(run_dir),
        )

        estimate = self._cost_estimator.estimate(spec)

        decision = self._policy.is_allowed(request, estimate)
        if not decision.allowed:
            return ExperimentResult(
                run_id=run_id,
                success=False,
                rejected=True,
                rejection_reason=decision.reason,
                cost_estimate=estimate,
            )

        repo = GitRepo()
        repo.init(run_dir)
        repo.commit([code_file], f"experiment code for {run_id}")

        run_log = self._executor.run(spec, estimate)

        cost_actual = CostActual(
            cpu_seconds=run_log.cpu_seconds,
            memory_mb=run_log.peak_memory_mb,
            wall_seconds=run_log.wall_seconds,
            total_cost=(
                run_log.wall_seconds * 0.001
                + run_log.peak_memory_mb * 0.000001
            ),
        )

        self._cost_estimator.update(cost_actual)
        self._policy.record_spend(cost_actual.total_cost)

        results_file = run_dir / "results.txt"
        results_file.write_text(run_log.stdout)
        provenance = repo.commit([results_file], f"results for {run_id}")

        output_hash = hashlib.sha256(run_log.stdout.encode()).hexdigest()
        success = run_log.exit_code == 0 and not run_log.timed_out

        result = ExperimentResult(
            run_id=run_id,
            success=success,
            run_log=run_log,
            cost_estimate=estimate,
            cost_actual=cost_actual,
            provenance=provenance,
            output_hash=output_hash,
        )

        if self._auditor and success:
            result.audit = self._auditor.verify(result)

        return result

    def cancel(self, run_id: str) -> None:
        self._cancelled.add(run_id)
