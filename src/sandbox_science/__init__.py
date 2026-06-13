"""Budget-aware sandbox with Git provenance and reward-hacking mitigation."""

__version__ = "0.1.0"

from sandbox_science.auditor import AuditFlag, AuditReport, Auditor, CrossValReport
from sandbox_science.cost_model import CostActual, CostEstimate, CostEstimator, ExecutionSpec
from sandbox_science.executor import Executor, RunLog
from sandbox_science.policy import PolicyDecision, PolicyEngine
from sandbox_science.provenance import CommitInfo, GitRepo, MergeResult
from sandbox_science.sandbox import ExperimentRequest, ExperimentResult, Sandbox

__all__ = [
    "AuditFlag",
    "AuditReport",
    "Auditor",
    "CommitInfo",
    "CostActual",
    "CostEstimate",
    "CostEstimator",
    "CrossValReport",
    "ExecutionSpec",
    "Executor",
    "ExperimentRequest",
    "ExperimentResult",
    "GitRepo",
    "MergeResult",
    "PolicyDecision",
    "PolicyEngine",
    "RunLog",
    "Sandbox",
]
