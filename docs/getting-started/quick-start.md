# Quick‑Start Guide – **EurekaLab** (`sandbox_science`)

Welcome to **EurekaLab** – a self‑regulating, budget‑aware execution sandbox that tracks provenance with Git and protects against reward‑hacking.  
All public objects live under the top‑level package `sandbox_science`. The guide below shows how to install the library, initialise a sandbox, run an experiment, and inspect the audit & provenance information.

---

## 1. Installation

```bash
# Clone the repo (or add it as a submodule)
git clone https://github.com/yourorg/eureka_lab.git
cd eureka_lab

# Install the package in editable mode (includes the test suite)
pip install -e .
```

> **Tip** – The package follows the *src‑layout* (`src/sandbox_science`). After installation you can import it simply with `import sandbox_science`.

---

## 2. Core Concepts (at a glance)

| Module | Primary class / function | What it does |
|--------|--------------------------|--------------|
| `auditor` | `AuditFlag`, `AuditReport`, `CrossValReport`, `verify`, `cross_validate` | Checks results for correctness, reproducibility and reward‑hacking. |
| `cost_model` | `ExecutionSpec`, `CostEstimate`, `CostActual`, `estimate`, `update` | Predicts and records the computational cost of a run. |
| `executor` | `RunLog`, `run` | Executes a spec inside a resource‑limited sandbox. |
| `policy` | `PolicyDecision`, `is_allowed`, `record_spend`, `spent` | Enforces budget limits and decides whether a run may proceed. |
| `provenance` | `CommitInfo`, `MergeResult`, `init`, `commit`, `log`, `merge`, `path` | Handles a lightweight Git repo that stores experiment artefacts. |
| `sandbox` | `ExperimentRequest`, `ExperimentResult`, `submit`, `cancel` | High‑level façade that glues the above pieces together. |
| `utils.resource_limiter` | `apply`, `check_process` | OS‑level limits (CPU, memory) for a running process. |
| `utils.timer` | `start`, `stop`, `elapsed` | Simple wall‑clock timer used by the executor. |

All objects are **Pydantic** models (`BaseModel`) where appropriate, so they validate their fields automatically and can be serialised to JSON for logging.

---

## 3. Minimal Working Example

```python
# example_01_basic.py
from pathlib import Path
from sandbox_science import (
    ExperimentRequest,
    ExperimentResult,
    ExecutionSpec,
    CostEstimate,
    PolicyDecision,
    is_allowed,
    record_spend,
    spent,
    run,
    verify,
    init as prov_init,
    commit as prov_commit,
)

# ----------------------------------------------------------------------
# 1️⃣  Initialise provenance (a tiny Git repo in ./repo)
# ----------------------------------------------------------------------
repo_path = Path("./repo")
prov_init(repo_path)                     # creates .git if missing

# ----------------------------------------------------------------------
# 2️⃣  Define what we want to run
# ----------------------------------------------------------------------
spec = ExecutionSpec(
    command="python my_model.py --epochs 5",
    env={"PYTHONPATH": "."},
    resources={"cpu": 2, "mem_mb": 1024},
)

# ----------------------------------------------------------------------
# 3️⃣  Estimate the cost (e.g. 10 “credits”)
# ----------------------------------------------------------------------
estimate: CostEstimate = CostEstimate(credits=10.0)

# ----------------------------------------------------------------------
# 4️⃣  Policy check – is the run allowed under the current budget?
# ----------------------------------------------------------------------
policy = PolicyDecision(max_budget=estimate.credits, spent=spent())
if not is_allowed(policy):
    raise RuntimeError("Budget exhausted – cannot run experiment")

# ----------------------------------------------------------------------
# 5️⃣  Submit the experiment (high‑level façade)
# ----------------------------------------------------------------------
request = ExperimentRequest(
    spec=spec,
    budget=estimate,
    provenance_repo=repo_path,
    requester="alice@example.com",
)

result: ExperimentResult = ExperimentResult.parse_obj(
    {
        "run_id": "run-001",
        "status": "SUCCESS",
        "log": run(spec, estimate).dict(),
    }
)

# ----------------------------------------------------------------------
# 6️⃣  Record spend & provenance
# ----------------------------------------------------------------------
record_spend(result.log.cost)            # updates the policy budget
commit_info = prov_commit(
    files=[repo_path / "results/run-001.json"],
    message=f"Add result {result.run_id}",
)
print(f"Committed {commit_info.sha[:7]} – {commit_info.message}")

# ----------------------------------------------------------------------
# 7️⃣  Verify the outcome (detect reward‑hacking)
# ----------------------------------------------------------------------
audit = verify(result)
print(f"Audit flags: {audit.flags}")
```

**What you see in the script**

1. **Provenance** – a tiny Git repo is created (`prov_init`).  
2. **Spec** – a description of the command to run (`ExecutionSpec`).  
3. **Cost model** – we predict a budget (`CostEstimate`).  
4. **Policy** – `is_allowed` checks that the predicted spend does not exceed the remaining budget.  
5. **Execution** – `run` actually launches the command inside a sandbox (resource limits are applied automatically).  
6. **Spend tracking** – `record_spend` updates the policy’s internal counter.  
7. **Audit** – `verify` returns an `AuditReport` that flags any suspicious behaviour (e.g., unusually low loss, missing logs).

---

## 4. A Slightly More Advanced Workflow

```python
# example_02_cross_validation.py
from pathlib import Path
from sandbox_science import (
    ExecutionSpec,
    CostEstimate,
    ExperimentRequest,
    submit,
    cancel,
    cross_validate,
    verify,
    init as prov_init,
    log as prov_log,
)

# ----------------------------------------------------------------------
# Initialise provenance repo (once per project)
# ----------------------------------------------------------------------
repo = Path("./ml_repo")
prov_init(repo)

# ----------------------------------------------------------------------
# Build a list of 5 CV folds (different specs)
# ----------------------------------------------------------------------
folds = [
    ExecutionSpec(
        command=f"python train.py --fold {i}",
        env={},
        resources={"cpu": 1, "mem_mb": 512},
    )
    for i in range(5)
]

# ----------------------------------------------------------------------
# Submit each fold – collect the ExperimentResult objects
# ----------------------------------------------------------------------
results = [submit(ExperimentRequest(spec=s, budget=CostEstimate(credits=2.0), provenance_repo=repo))
           for s in folds]

# ----------------------------------------------------------------------
# Cross‑validate the collection of results
# ----------------------------------------------------------------------
cv_report = cross_validate([r for r in results])
print(f"Cross‑val mean accuracy: {cv_report.mean_accuracy:.2f}")

# ----------------------------------------------------------------------
# Verify each result individually (detect reward‑hacking per fold)
# ----------------------------------------------------------------------
for r in results:
    audit