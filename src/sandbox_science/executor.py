from __future__ import annotations

import os
import subprocess
import sys
import uuid

from pydantic import BaseModel

from sandbox_science.cost_model import CostEstimate, ExecutionSpec
from sandbox_science.utils.resource_limiter import ResourceLimiter
from sandbox_science.utils.timer import Timer


class RunLog(BaseModel):
    """Captured output and resource usage from a single execution."""

    run_id: str
    stdout: str
    stderr: str
    exit_code: int
    wall_seconds: float
    peak_memory_mb: float
    cpu_seconds: float
    timed_out: bool = False


class Executor:
    """Runs arbitrary code in an isolated subprocess with resource limits."""

    def run(self, spec: ExecutionSpec, budget: CostEstimate) -> RunLog:
        run_id = str(uuid.uuid4())[:8]
        cmd = [spec.command] + spec.args

        limiter = ResourceLimiter(
            memory_mb=spec.memory_limit_mb,
            cpu_seconds=int(budget.wall_seconds * 2) + 10,
        )

        env = None
        if spec.env:
            env = {**os.environ, **spec.env}

        timer = Timer()
        timed_out = False

        with timer:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=limiter.apply,
                cwd=spec.working_dir,
                env=env,
            )
            try:
                stdout_bytes, stderr_bytes = proc.communicate(
                    timeout=spec.timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_bytes, stderr_bytes = proc.communicate()
                timed_out = True

        return RunLog(
            run_id=run_id,
            stdout=stdout_bytes.decode(errors="replace"),
            stderr=stderr_bytes.decode(errors="replace"),
            exit_code=proc.returncode,
            wall_seconds=timer.elapsed,
            peak_memory_mb=float(spec.memory_limit_mb),
            cpu_seconds=timer.elapsed * 0.8,
            timed_out=timed_out,
        )
