# EurekaLab

**Budget‑aware sandbox for autonomous scientific discovery with provenance.**

EurekaLab (`sandbox_science`) wraps untrusted, agent‑generated code in a budget‑aware execution environment. It estimates and enforces a cost budget before running, captures every run in a Git‑backed provenance store, and audits results for reward‑hacking — turning the execution environment itself into a first‑class, reusable abstraction.

## Quick Start

```python
import tempfile
from sandbox_science import Sandbox, ExperimentRequest

# A sandbox enforces a cost budget and records provenance
sandbox = Sandbox(workspace=tempfile.mkdtemp())

request = ExperimentRequest(
    code="print('hello from the sandbox')",
    budget=10.0,
    timeout_seconds=5,
    memory_limit_mb=256,
)

result = sandbox.submit(request)
print(result.success)                  # True
print(result.run_log.stdout.strip())   # hello from the sandbox
print(result.cost_actual.total_cost)   # measured cost, <= budget
```

See [Installation](getting-started/installation.md) and the [Quick Start guide](getting-started/quick-start.md) to go further, or the [API Reference](reference.md).
