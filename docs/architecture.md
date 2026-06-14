# Architecture

EurekaLab is organized around a small set of modules that form a pipeline:

```mermaid
flowchart LR
    A["Cost model"]
    B["Policy engine"]
    C["Executor"]
    D["Provenance"]
    E["Auditor"]
    A --> B
    B --> C
    C --> D
    D --> E
```

## Modules

| Module | Description |
|--------|-------------|
| `auditor` | — |
| `cost_model` | — |
| `executor` | — |
| `policy` | — |
| `provenance` | — |
| `sandbox` | — |
