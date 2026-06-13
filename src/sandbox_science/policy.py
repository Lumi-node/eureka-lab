from __future__ import annotations

from pydantic import BaseModel

from sandbox_science.cost_model import CostEstimate


class PolicyDecision(BaseModel):
    """Whether a request is admissible, with reasoning."""

    allowed: bool
    reason: str = ""
    adjusted_budget: float | None = None
    warnings: list[str] = []


class ExperimentRequestLike:
    """Structural type expected by the policy engine (avoids circular import)."""

    code: str
    budget: float


class PolicyEngine:
    """Central admission controller: budget, safety, and anti-hacking rules."""

    BLOCKED_COMMANDS = ("rm -rf", "sudo", "mkfs", "dd if=", "chmod 777")

    def __init__(self, budget_limit: float = 100.0) -> None:
        self._budget_limit = budget_limit
        self._spent: float = 0.0

    def is_allowed(
        self,
        request: ExperimentRequestLike,
        estimate: CostEstimate | None = None,
    ) -> PolicyDecision:
        for cmd in self.BLOCKED_COMMANDS:
            if cmd in request.code:
                return PolicyDecision(
                    allowed=False,
                    reason=f"Blocked command pattern: {cmd!r}",
                )

        if estimate is not None:
            if estimate.total_cost > request.budget:
                return PolicyDecision(
                    allowed=False,
                    reason=(
                        f"Estimated cost {estimate.total_cost:.6f} "
                        f"exceeds request budget {request.budget:.6f}"
                    ),
                )
            if self._spent + estimate.total_cost > self._budget_limit:
                return PolicyDecision(
                    allowed=False,
                    reason=(
                        f"Would exceed global budget limit "
                        f"({self._spent:.4f} + {estimate.total_cost:.4f} "
                        f"> {self._budget_limit:.4f})"
                    ),
                )

        return PolicyDecision(allowed=True)

    def record_spend(self, cost: float) -> None:
        self._spent += cost

    @property
    def spent(self) -> float:
        return self._spent
