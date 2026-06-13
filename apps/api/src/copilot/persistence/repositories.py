from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

import httpx

from copilot.domain.models import Analysis


class AnalysisRepository(Protocol):
    async def create(self, analysis: Analysis) -> Analysis: ...

    async def list(self, owner_id: UUID) -> Sequence[Analysis]: ...

    async def get(self, analysis_id: UUID, owner_id: UUID) -> Analysis | None: ...

    async def update(self, analysis: Analysis) -> Analysis: ...

    async def delete(self, analysis_id: UUID, owner_id: UUID) -> bool: ...


class InMemoryAnalysisRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, Analysis] = {}

    async def create(self, analysis: Analysis) -> Analysis:
        self._items[analysis.id] = analysis.model_copy(deep=True)
        return analysis

    async def list(self, owner_id: UUID) -> Sequence[Analysis]:
        return sorted(
            (
                item.model_copy(deep=True)
                for item in self._items.values()
                if item.owner_id == owner_id
            ),
            key=lambda item: item.updated_at,
            reverse=True,
        )

    async def get(self, analysis_id: UUID, owner_id: UUID) -> Analysis | None:
        item = self._items.get(analysis_id)
        if item is None or item.owner_id != owner_id:
            return None
        return item.model_copy(deep=True)

    async def update(self, analysis: Analysis) -> Analysis:
        updated = analysis.model_copy(update={"updated_at": datetime.now(UTC)})
        self._items[updated.id] = updated.model_copy(deep=True)
        return updated

    async def delete(self, analysis_id: UUID, owner_id: UUID) -> bool:
        item = self._items.get(analysis_id)
        if item is None or item.owner_id != owner_id:
            return False
        del self._items[analysis_id]
        return True


class SupabaseAnalysisRepository:
    """PostgREST adapter that forwards the user's JWT so database RLS applies."""

    def __init__(self, base_url: str, publishable_key: str, access_token: str) -> None:
        self._url = f"{base_url.rstrip('/')}/rest/v1/analyses"
        self._headers = {
            "apikey": publishable_key,
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json",
        }

    async def create(self, analysis: Analysis) -> Analysis:
        response = await self._request(
            "POST",
            self._url,
            headers={**self._headers, "prefer": "return=representation"},
            json=_analysis_row(analysis),
        )
        return _analysis_from_row(response.json()[0])

    async def list(self, owner_id: UUID) -> Sequence[Analysis]:
        response = await self._request(
            "GET",
            self._url,
            headers=self._headers,
            params={
                "select": "*",
                "owner_id": f"eq.{owner_id}",
                "order": "updated_at.desc",
            },
        )
        return [_analysis_from_row(row) for row in response.json()]

    async def get(self, analysis_id: UUID, owner_id: UUID) -> Analysis | None:
        response = await self._request(
            "GET",
            self._url,
            headers=self._headers,
            params={
                "select": "*",
                "id": f"eq.{analysis_id}",
                "owner_id": f"eq.{owner_id}",
                "limit": "1",
            },
        )
        rows = response.json()
        return _analysis_from_row(rows[0]) if rows else None

    async def update(self, analysis: Analysis) -> Analysis:
        updated = analysis.model_copy(update={"updated_at": datetime.now(UTC)})
        response = await self._request(
            "PATCH",
            self._url,
            headers={**self._headers, "prefer": "return=representation"},
            params={"id": f"eq.{analysis.id}", "owner_id": f"eq.{analysis.owner_id}"},
            json=_analysis_row(updated),
        )
        rows = response.json()
        if not rows:
            raise LookupError(str(analysis.id))
        return _analysis_from_row(rows[0])

    async def delete(self, analysis_id: UUID, owner_id: UUID) -> bool:
        response = await self._request(
            "DELETE",
            self._url,
            headers={**self._headers, "prefer": "return=representation"},
            params={"id": f"eq.{analysis_id}", "owner_id": f"eq.{owner_id}"},
        )
        return bool(response.json())

    @staticmethod
    async def _request(
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        params: Mapping[str, str] | None = None,
        json: dict[str, object] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json,
            )
        response.raise_for_status()
        return response


def _analysis_row(analysis: Analysis) -> dict[str, object]:
    return {
        "id": str(analysis.id),
        "owner_id": str(analysis.owner_id),
        "title": analysis.title,
        "status": analysis.status.value,
        "trial": analysis.trial.model_dump(mode="json"),
        "created_at": analysis.created_at.isoformat(),
        "updated_at": analysis.updated_at.isoformat(),
    }


def _analysis_from_row(row: dict[str, object]) -> Analysis:
    return Analysis.model_validate(row)
