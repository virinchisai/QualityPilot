"""Extension contracts for QualityPilot runners and integrations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from qualitypilot.models.analysis import FailureAnalysis, FailureInput
from qualitypilot.models.test_case import GenerationResult, Requirement


class RequirementSourceAdapter(ABC):
    @abstractmethod
    def ingest(self, content: str, source_format: str) -> list[Requirement]: ...


class TestCaseGeneratorAdapter(ABC):
    @abstractmethod
    def generate(self, requirement: Requirement) -> GenerationResult: ...


class CommandTestAdapter(ABC):
    @abstractmethod
    def command(self) -> list[str]: ...


class UITestAdapter(CommandTestAdapter):
    pass


class APITestAdapter(CommandTestAdapter):
    pass


class BDDAdapter(CommandTestAdapter):
    pass


class SecurityTestAdapter(CommandTestAdapter):
    pass


class LoadTestAdapter(CommandTestAdapter):
    pass


class AIQualityAdapter(ABC):
    @abstractmethod
    def evaluate(self, case: dict[str, Any]) -> dict[str, Any]: ...


class EvidenceCollectorAdapter(ABC):
    @abstractmethod
    def collect(self, paths: list[Path]) -> dict[str, Any]: ...


class FailureAnalyzerAdapter(ABC):
    @abstractmethod
    def analyze(self, failure: FailureInput) -> FailureAnalysis: ...


class ReporterAdapter(ABC):
    @abstractmethod
    def render(self, value: Any) -> str: ...


class DefectTrackerAdapter(ABC):
    @abstractmethod
    def create_payload(self, value: Any) -> dict[str, Any]: ...
