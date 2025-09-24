"""HTTP clients for CopilotKit and Tongyi DeepResearch integrations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from helpers.serialization import to_serializable


@dataclass
class IntegrationResult:
    """Normalized response metadata returned by integration clients."""

    status: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"status": self.status}
        if self.data is not None:
            payload["data"] = self.data
        if self.error is not None:
            payload["error"] = self.error
        return payload


class _BaseClient:
    """Shared helper for HTTP-based integrations."""

    def __init__(
        self,
        name: str,
        api_base: Optional[str],
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.name = name
        self.api_base = (api_base or "").rstrip("/") or None
        self.api_key = api_key
        self.endpoint = endpoint or ""
        self.timeout = timeout
        self.session = session or requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.api_base)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _resolve_url(self) -> Optional[str]:
        if not self.api_base:
            return None
        if not self.endpoint:
            return self.api_base
        if self.endpoint.startswith("http"):
            return self.endpoint
        return f"{self.api_base}{self.endpoint if self.endpoint.startswith('/') else '/' + self.endpoint}"

    def _post(self, payload: Dict[str, Any]) -> IntegrationResult:
        url = self._resolve_url()
        if not url:
            return IntegrationResult(status="disabled")
        try:
            response = self.session.post(
                url,
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return IntegrationResult(
                    status="error", error=f"{self.name} returned non-dict payload"
                )
            return IntegrationResult(status="ok", data=data)
        except requests.exceptions.RequestException as exc:
            return IntegrationResult(status="error", error=str(exc))
        except ValueError:
            return IntegrationResult(status="error", error="Invalid JSON response")


class CopilotKitClient(_BaseClient):
    """Client wrapper for CopilotKit hosted copilots."""

    def __init__(
        self,
        api_base: Optional[str],
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        super().__init__(
            name="CopilotKit",
            api_base=api_base,
            api_key=api_key,
            endpoint=endpoint,
            timeout=timeout,
            session=session,
        )

    def request_brief(self, summary: Dict[str, Any]) -> IntegrationResult:
        payload = {"summary": to_serializable(summary), "source": "InsightFactory"}
        return self._post(payload)


class TongyiDeepResearchClient(_BaseClient):
    """Client wrapper for Tongyi DeepResearch orchestrations."""

    def __init__(
        self,
        api_base: Optional[str],
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 30,
        session: Optional[requests.Session] = None,
    ) -> None:
        super().__init__(
            name="Tongyi DeepResearch",
            api_base=api_base,
            api_key=api_key,
            endpoint=endpoint,
            timeout=timeout,
            session=session,
        )

    def request_research(self, summary: Dict[str, Any]) -> IntegrationResult:
        payload = {"summary": to_serializable(summary), "mode": "manufacturing-ops"}
        return self._post(payload)


__all__ = [
    "CopilotKitClient",
    "TongyiDeepResearchClient",
    "IntegrationResult",
]
