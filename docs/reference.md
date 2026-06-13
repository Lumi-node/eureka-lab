# EurekaLab – `sandbox_science` API Reference

The **sandbox_science** package implements a budget‑aware execution sandbox with provenance tracking and audit capabilities.  
All public symbols are listed below exactly as they appear in the source tree.  
Only the items shown in the *Actual API* section are documented – no extra functions or classes are invented.

---

## `src/sandbox_science/auditor.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`AuditFlag`** | `class AuditFlag(str, Enum)` | Enum of possible audit outcomes (e.g., `PASS`, `FAIL`, `WARN`). |
| **`AuditReport`** | `class AuditReport(BaseModel)` | Pydantic model that summarises the result of a single audit run. |
| **`CrossValReport`** | `class CrossValReport(BaseModel)` | Pydantic model that summarises cross‑validation of many audit results. |
| **`verify`** | `def verify(self, result: _ResultLike) -> AuditReport` | Runs the auditor on a single execution result and returns an `AuditReport`. |
| **`cross_validate`** | `def cross_validate(self, results: list[_ResultLike]) -> CrossValReport` | Performs cross‑validation over a collection of results, producing a `CrossValReport`. |

### Example

```python
from sandbox_science.auditor import Auditor, AuditFlag

auditor = Auditor()
result = {"output": 42, "metadata": {...}}   # any _ResultLike object
report = auditor.verify(result)

print(report)                     # -> AuditReport(...)
print(report.status)              # e.g. AuditFlag.PASS
```

---

## `src/sandbox_science/cost_model.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`ExecutionSpec`** | `class ExecutionSpec(BaseModel)` | Specification of a computation (e.g., command, resources, input data). |
| **`CostEstimate`** | `class CostEstimate(BaseModel)` | Predicted cost (time, CPU, memory, monetary) for an `ExecutionSpec`. |
| **`CostActual`** | `class CostActual(BaseModel)` | Observed cost after execution. |
| **`estimate`** | `def estimate(self, spec: ExecutionSpec) -> CostEstimate` | Produces a `CostEstimate` from a given `ExecutionSpec`. |
| **`update`** | `def update(self, actual: CostActual) -> None` | Incorporates a realised `CostActual` into the model (e.g., for learning). |

### Example

```python
from sandbox_science.cost_model import CostModel, ExecutionSpec

spec = ExecutionSpec(command="python train.py", cpu=2, memory_gb=4)
model = CostModel()
estimate = model.estimate(spec)

print(f"Predicted runtime: {estimate.runtime_seconds}s")
# later, after the run:
# model.update(CostActual(runtime_seconds=123, cpu_seconds=246, ...))
```

---

## `src/sandbox_science/executor.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`RunLog`** | `class RunLog(BaseModel)` | Log of a single execution, containing timestamps, exit code, and cost data. |
| **`run`** | `def run(self, spec: ExecutionSpec, budget: CostEstimate) -> RunLog` | Executes the given `ExecutionSpec` while respecting the supplied budget; returns a `RunLog`. |

### Example

```python
from sandbox_science.executor import Executor, RunLog
from sandbox_science.cost_model import ExecutionSpec, CostEstimate

spec = ExecutionSpec(command="python script.py", cpu=1, memory_gb=2)
budget = CostEstimate(runtime_seconds=300)   # 5‑minute budget

executor = Executor()
log: RunLog = executor.run(spec, budget)

print(log.exit_code, log.runtime_seconds)
```

---

## `src/sandbox_science/policy.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`PolicyDecision`** | `class PolicyDecision(BaseModel)` | Result of a policy check (allowed flag, reason, etc.). |
| **`is_allowed`** | `def is_allowed(self, cost: float) -> PolicyDecision` | Determines whether a new cost would exceed the policy limits. |
| **`record_spend`** | `def record_spend(self, cost: float) -> None` | Registers a spent amount against the policy’s budget. |
| **`spent`** | `def spent(self) -> float` | Returns the total amount spent so far. |

### Example

```python
from sandbox_science.policy import Policy

policy = Policy(max_budget=1000.0)   # $1000 budget
decision = policy.is_allowed(200.0)

if decision.allowed:
    policy.record_spend(200.0)

print(f"Total spent: ${policy.spent():.2f}")
```

---

## `src/sandbox_science/provenance.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`CommitInfo`** | `class CommitInfo(BaseModel)` | Information about a single Git commit (hash, author, message, timestamp). |
| **`MergeResult`** | `class MergeResult(BaseModel)` | Outcome of a merge operation (merged commit hash, conflicts, etc.). |
| **`path`** | `def path(self) -> Path` | Returns the filesystem path of the managed repository. |
| **`init`** | `def init(self, path: Path) -> None` | Initializes a new Git repository at `path`. |
| **`commit`** | `def commit(self, files: list[Path], message: str) -> CommitInfo` | Stages `files` and creates a commit with `message`. |
| **`log`** | `def log(self) -> list[CommitInfo]` | Returns the commit history as a list of `CommitInfo`. |
| **`merge`** | `def merge(self, other: GitRepo) -> MergeResult` | Merges another repository (`other`) into the current one, returning a `MergeResult`. |

### Example

```python
from pathlib import Path
from sandbox_science.provenance import Provenance

repo = Provenance()
repo.init(Path("/tmp/my_experiment"))

repo.commit([Path("data.csv"), Path("script.py")],
            "Initial data and script")

history = repo.log()
print(history[-1].message)   # -> "Initial data and script"
```

---

## `src/sandbox_science/sandbox.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`ExperimentRequest`** | `class ExperimentRequest(BaseModel)` | Request object describing an experiment (spec, budget, metadata). |
| **`ExperimentResult`** | `class ExperimentResult(BaseModel)` | Result object containing the outcome, logs, provenance, and audit report. |
| **`submit`** | `def submit(self, request: ExperimentRequest) -> ExperimentResult` | Submits an experiment to the sandbox; runs it respecting policy and budget, then returns an `ExperimentResult`. |
| **`cancel`** | `def cancel(self, run_id: str) -> None` | Cancels a running experiment identified by `run_id`. |

### Example

```python
from sandbox_science.sandbox import Sandbox, ExperimentRequest

sandbox = Sandbox()
req = ExperimentRequest(
    spec=ExecutionSpec(command="python train.py", cpu=2, memory_gb=8),
    budget=CostEstimate(runtime_seconds=600)
)

result = sandbox.submit(req)
print(result.status, result.audit_report.status)
```

---

## `src/sandbox_science/utils/resource_limiter.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`apply`** | `def apply(self) -> None` | Enforces the configured resource limits (CPU, memory, etc.) on the current process. |
| **`check_process`** | `def check_process(self, pid: int) -> dict[str, float]` | Returns a snapshot of resource usage for the given process ID (`pid`). |

### Example

```python
from sandbox_science.utils.resource_limiter import ResourceLimiter

limiter = ResourceLimiter(cpu_limit=1.0, memory_mb=512)
limiter.apply()                     # limit the current process

usage = limiter.check_process(pid=12345)
print(usage)                        # {'cpu_percent': 0.7, 'memory_mb': 300.2}
```

---

## `src/sandbox_science/utils/timer.py`

| Symbol | Signature | Description |
|--------|-----------|-------------|
| **`start`** | `def start(self) -> None` | Starts the timer. |
| **`stop`** | `def stop(self) -> float` | Stops the timer and returns the elapsed time in seconds. |
| **`elapsed`** | `def elapsed(self) -> float` | Returns the time elapsed since `start` without stopping the timer. |

### Example

```python
from sandbox_science.utils.timer