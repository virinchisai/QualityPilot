"""Evidence manifest generation without copying sensitive artifacts."""

import hashlib
from pathlib import Path

from qualitypilot.adapters.base import EvidenceCollectorAdapter


class ManifestEvidenceCollector(EvidenceCollectorAdapter):
    def collect(self, paths: list[Path]) -> dict:
        artifacts = []
        for path in paths:
            if path.is_file() and path.name not in {"storage-state.json"}:
                artifacts.append(
                    {
                        "path": str(path),
                        "size": path.stat().st_size,
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
        return {"artifacts": artifacts, "count": len(artifacts)}
