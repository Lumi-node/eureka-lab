<p align="center">
  <img src="assets/hero.jpg" alt="EurekaLab" width="900">
</p>

<h1 align="center">EurekaLab</h1>

<p align="center"><strong>Budget‑aware sandbox for autonomous scientific discovery with provenance.</strong></p>

<p align="center">
  <a href="https://github.com/Lumi-node/eureka-lab"><img src="https://img.shields.io/badge/GitHub-Repo-blue?logo=github" alt="GitHub"></a>
  <a href="https://github.com/Lumi-node/eureka-lab/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Lumi-node/eureka-lab/actions"><img src="https://img.shields.io/badge/tests-14-success.svg" alt="Tests"></a>
  <a href="https://lumi-node.github.io/eureka-lab/"><img src="https://img.shields.io/badge/docs-online-blue.svg" alt="Docs"></a>
</p>

---

EurekaLab (`sandbox_science`) wraps untrusted, agent‑generated code in a budget‑aware execution environment. It estimates and enforces a cost budget before running, captures every run in a Git‑backed provenance store, and audits results for reward‑hacking — turning the execution environment itself into a first‑class, reusable abstraction.

## Installation

```bash
pip install git+https://github.com/Lumi-node/eureka-lab.git
```

Requires Python ≥ 3.10. To work on the project locally:

```bash
git clone https://github.com/Lumi-node/eureka-lab.git
cd eureka-lab
pip install -e ".[dev]"
pytest -q
```

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

## Features

- **Budget‑aware execution** — estimate and enforce cost limits before a run starts
- **Git‑backed provenance** — every run committed for full reproducibility
- **Reward‑hacking auditor** with cross‑validation
- **Pluggable cost model and policy engine**

## Modules

| Module | Description |
|--------|-------------|
| `auditor` | — |
| `cost_model` | — |
| `executor` | — |
| `policy` | — |
| `provenance` | — |
| `sandbox` | — |

## Documentation

📖 Full documentation: [https://lumi-node.github.io/eureka-lab/](https://lumi-node.github.io/eureka-lab/)
📄 Technical paper: see [`paper/`](paper/) for the LaTeX source and compiled PDF.

> This is a reference implementation produced by an autonomous research pipeline. It is not published to PyPI; install from source as shown above.

## License

[MIT](LICENSE) © Andrew Young / Automate Capture Research
