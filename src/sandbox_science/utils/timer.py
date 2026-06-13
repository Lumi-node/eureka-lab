from __future__ import annotations

import time


class Timer:
    """Wall-clock timer with context-manager support."""

    def __init__(self) -> None:
        self._start: float | None = None
        self._elapsed: float = 0.0

    def start(self) -> None:
        self._start = time.monotonic()

    def stop(self) -> float:
        if self._start is not None:
            self._elapsed = time.monotonic() - self._start
            self._start = None
        return self._elapsed

    @property
    def elapsed(self) -> float:
        if self._start is not None:
            return time.monotonic() - self._start
        return self._elapsed

    def __enter__(self) -> Timer:
        self.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()
