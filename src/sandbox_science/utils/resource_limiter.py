from __future__ import annotations


class ResourceLimiter:
    """Sets OS-level resource limits on child processes (Linux)."""

    def __init__(self, memory_mb: int = 1024, cpu_seconds: int = 300) -> None:
        self.memory_mb = memory_mb
        self.cpu_seconds = cpu_seconds

    def apply(self) -> None:
        """Call as *preexec_fn* of subprocess.Popen."""
        try:
            import resource as _resource

            _resource.setrlimit(
                _resource.RLIMIT_CPU,
                (self.cpu_seconds, self.cpu_seconds + 5),
            )
        except (ImportError, ValueError, OSError):
            pass

    def check_process(self, pid: int) -> dict[str, float]:
        try:
            import psutil

            proc = psutil.Process(pid)
            mem = proc.memory_info()
            return {
                "rss_mb": mem.rss / (1024 * 1024),
                "vms_mb": mem.vms / (1024 * 1024),
            }
        except Exception:
            return {}
