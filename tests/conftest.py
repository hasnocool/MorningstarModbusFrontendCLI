"""Pytest hooks used to make CI failures visible in GitHub check annotations."""

from __future__ import annotations

import os

import pytest


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Emit a GitHub error annotation for failed test phases when running in Actions."""

    if os.environ.get("GITHUB_ACTIONS") != "true" or not report.failed:
        return
    path, line, _ = report.location
    message = str(report.longrepr)
    message = (
        message.replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )
    print(f"::error file={path},line={line + 1}::{message}")
