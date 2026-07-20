"""Selenium compatibility adapter for legacy enterprise UI suites."""

import os

from qualitypilot.adapters.base import UITestAdapter


class SeleniumWebDriverAdapter(UITestAdapter):
    """Expose the opt-in Selenium smoke suite through the common UI contract."""

    def command(self) -> list[str]:
        python = os.getenv("QUALITYPILOT_PYTHON", ".venv/bin/python")
        return [python, "-m", "pytest", "tests/selenium", "-m", "selenium", "-q"]
