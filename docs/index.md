# EurekaLab

<div align="center">
  <h1 style="font-size: 3.5rem; margin-bottom: 0.5rem;">EurekaLab</h1>
  <p style="font-size: 1.25rem; color: #555;">Budget‑aware sandbox for autonomous scientific discovery with provenance.</p>
  <a href="getting-started.md" class="md-button md-button--primary" style="margin-top: 1rem;">Get Started</a>
</div>

---

## 🚀 Features

<div class="md-grid md-typeset">

### Budget‑Aware Execution Sandbox
<div class="md-card">
  <p>Self‑regulating runtime that respects a configurable compute budget (CPU, GPU, memory, and wall‑time). The sandbox automatically throttles or aborts tasks that exceed limits, ensuring reproducible experiments without resource overruns.</p>
</div>

### Provenance‑Tracked Collaboration
<div class="md-card">
  <p>All artifacts, code, and configuration are versioned with Git. Automatic provenance metadata (author, timestamps, input/output hashes) is attached to every run, enabling full traceability and reproducible science.</p>
</div>

### Reward‑Hacking Mitigation
<div class="md-card">
  <p>Built‑in detection of reward‑gaming strategies. The sandbox monitors metric drift, anomalous reward spikes, and policy loops, and can intervene or flag suspicious runs.</p>
</div>

### Clean Python API (src layout)
<div class="md-card">
  <p>Import the library with a tidy namespace: <code>import sandbox_science as es</code>. The package follows the modern <code>src/</code> layout, includes type hints, and is ready for integration into any research pipeline.</p>
</div>

</div>

---

## 📦 Quick Install

```bash
pip install sandbox_science
```

---

## 📖 Getting Started

Dive into the tutorial to set up your first budget‑aware experiment, track provenance, and see reward‑hacking protection in action:

[Getting Started →](getting-started.md)

--- 

*Built with ❤️ using [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/).*