# Quick Start

The following example runs end‑to‑end against the installed package:

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

For the full public API, see the [API Reference](../reference.md). For how the
pieces fit together, see [Architecture](../architecture.md).
