"""Allow-listed local command execution for known test suites."""

import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

SUITES = {
    "unit": [".venv/bin/pytest", "tests/unit", "-q"],
    "api": [".venv/bin/pytest", "tests/api", "-q"],
    "identity": [".venv/bin/pytest", "tests/identity", "tests/security", "-q"],
    "bdd": [".venv/bin/behave", "tests/bdd"],
    "playwright": ["npx", "playwright", "test", "--project=chromium"],
}


@dataclass
class ExecutionResult:
    execution_id: str
    suite: str
    status: str
    duration_seconds: float
    exit_code: int
    output: str


def run_suite(suite: str, root: Path, timeout: int = 600) -> ExecutionResult:
    if suite not in SUITES:
        raise ValueError(f"suite must be one of {', '.join(SUITES)}")
    started = time.perf_counter()
    completed = subprocess.run(
        SUITES[suite],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )  # noqa: S603
    return ExecutionResult(
        str(uuid.uuid4()),
        suite,
        "passed" if completed.returncode == 0 else "failed",
        time.perf_counter() - started,
        completed.returncode,
        completed.stdout[-20_000:],
    )
