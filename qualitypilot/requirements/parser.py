"""Safe, deterministic normalization for supported requirement sources."""

import json
import re
from hashlib import sha1
from typing import Any

import yaml

from qualitypilot.adapters.base import RequirementSourceAdapter
from qualitypilot.models.test_case import Requirement


def _stable_id(title: str) -> str:
    return f"REQ-{sha1(title.encode()).hexdigest()[:8].upper()}"  # noqa: S324 - identifier only


class LocalRequirementAdapter(RequirementSourceAdapter):
    def ingest(self, content: str, source_format: str) -> list[Requirement]:
        fmt = source_format.lower().lstrip(".")
        if fmt in {"yaml", "yml"}:
            return self._structured(yaml.safe_load(content), fmt)
        if fmt == "json":
            return self._structured(json.loads(content), fmt)
        if fmt in {"openapi", "openapi-yaml", "openapi-json"}:
            raw = (
                json.loads(content) if content.lstrip().startswith("{") else yaml.safe_load(content)
            )
            return self._openapi(raw)
        if fmt in {"gherkin", "feature"}:
            return self._gherkin(content)
        if fmt in {"markdown", "md"}:
            return self._markdown(content)
        if fmt in {"text", "txt", "plain"}:
            title = content.strip().splitlines()[0][:250]
            return [
                Requirement(
                    id=_stable_id(title),
                    title=title,
                    description=content.strip(),
                    source_format="text",
                )
            ]
        raise ValueError(f"unsupported requirement format: {source_format}")

    def _structured(self, raw: Any, fmt: str) -> list[Requirement]:
        items = raw.get("requirements", [raw]) if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            raise ValueError("structured input must be a requirement object or list")
        result = []
        for item in items:
            title = str(item.get("title") or item.get("name") or "Untitled requirement")
            result.append(
                Requirement(
                    id=str(item.get("id") or _stable_id(title)),
                    title=title,
                    description=str(item.get("description") or title),
                    acceptance_criteria=[str(x) for x in item.get("acceptance_criteria", [])],
                    source_format=fmt,
                    metadata=item.get("metadata", {}),
                )
            )
        return result

    def _markdown(self, content: str) -> list[Requirement]:
        sections = re.split(r"(?m)^#{1,3}\s+", content)
        requirements = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            title, *body = section.splitlines()
            description = "\n".join(body).strip() or title
            criteria = [
                re.sub(r"^[-*]\s+", "", line) for line in body if re.match(r"^[-*]\s+", line)
            ]
            requirements.append(
                Requirement(
                    id=_stable_id(title),
                    title=title[:250],
                    description=description,
                    acceptance_criteria=criteria,
                    source_format="markdown",
                )
            )
        return requirements

    def _gherkin(self, content: str) -> list[Requirement]:
        title = "Gherkin feature"
        scenarios: list[str] = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("Feature:") and title == "Gherkin feature":
                candidate = stripped.removeprefix("Feature:").strip()
                if candidate:
                    title = candidate
                continue
            for prefix in ("Scenario Outline:", "Scenario:"):
                if stripped.startswith(prefix):
                    candidate = stripped.removeprefix(prefix).strip()
                    if candidate:
                        scenarios.append(candidate)
                    break
        return [
            Requirement(
                id=_stable_id(title),
                title=title,
                description=content.strip(),
                acceptance_criteria=scenarios,
                source_format="gherkin",
            )
        ]

    def _openapi(self, raw: dict[str, Any]) -> list[Requirement]:
        requirements = []
        for path, methods in raw.get("paths", {}).items():
            for method, operation in methods.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                title = operation.get("summary") or f"{method.upper()} {path}"
                requirements.append(
                    Requirement(
                        id=operation.get("operationId") or _stable_id(f"{method}:{path}"),
                        title=title,
                        description=operation.get("description")
                        or f"Validate {method.upper()} {path}",
                        acceptance_criteria=[
                            f"Returns documented status {code}"
                            for code in operation.get("responses", {})
                        ],
                        source_format="openapi",
                        metadata={"method": method.upper(), "endpoint": path},
                    )
                )
        return requirements
