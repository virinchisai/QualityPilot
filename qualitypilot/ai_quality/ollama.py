"""Optional local Ollama summary provider."""

import httpx


class OllamaSummaryProvider:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url, self.model = base_url.rstrip("/"), model

    def summarize(self, deterministic_analysis: dict, timeout: float = 15) -> str:
        prompt = (
            "Summarize this deterministic test failure classification without "
            "changing its verdict: " + str(deterministic_analysis)
        )
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        response.raise_for_status()
        return str(response.json()["response"])
