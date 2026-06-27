from dataclasses import dataclass
from typing import Callable, Optional


class AWA05Error(Exception):
    """Base exception for AWA05 application-level errors."""


@dataclass
class JobResult:
    """Structured result for scheduler-style protected jobs."""

    name: str
    ok: bool
    error: Optional[BaseException] = None

    @property
    def failed(self):
        return not self.ok

    @property
    def error_type(self):
        return type(self.error).__name__ if self.error else None

    @property
    def message(self):
        return str(self.error) if self.error else ""


def run_safely(name: str, job: Callable[[], object]) -> JobResult:
    try:
        job()
        return JobResult(name=name, ok=True)
    except Exception as exc:
        return JobResult(name=name, ok=False, error=exc)
