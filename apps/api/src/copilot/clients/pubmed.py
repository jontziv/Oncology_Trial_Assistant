import asyncio
from datetime import UTC, datetime
from typing import Any

import httpx

from copilot.clients.clinical_trials import UpstreamUnavailableError
from copilot.domain.models import EvidenceSource, PublicationEvidence


class PubMedClient:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str = "",
        tool: str = "oncology_trial_feasibility_copilot",
        email: str = "",
        timeout_seconds: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._tool = tool
        self._email = email
        self._timeout = timeout_seconds
        self._client = client

    async def search(
        self,
        query: str,
        *,
        limit: int = 8,
    ) -> tuple[list[PublicationEvidence], list[EvidenceSource]]:
        common = {
            "db": "pubmed",
            "retmode": "json",
            "tool": self._tool,
        }
        if self._email:
            common["email"] = self._email
        if self._api_key:
            common["api_key"] = self._api_key

        search = await self._request(
            "/esearch.fcgi",
            params={
                **common,
                "term": query,
                "retmax": str(min(max(limit, 1), 20)),
                "sort": "relevance",
            },
        )
        ids = search.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return [], []
        await asyncio.sleep(0.12 if self._api_key else 0.34)
        summary = await self._request(
            "/esummary.fcgi",
            params={**common, "id": ",".join(ids)},
        )
        return _map_summaries(summary.json(), ids)

    async def _request(self, path: str, *, params: dict[str, str]) -> httpx.Response:
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self._timeout)
        try:
            response = await client.get(f"{self._base_url}{path}", params=params)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise UpstreamUnavailableError("PubMed unavailable") from exc
        finally:
            if owns_client:
                await client.aclose()
        if response.status_code >= 400:
            raise UpstreamUnavailableError(
                f"PubMed returned HTTP {response.status_code}"
            )
        return response


def _map_summaries(
    payload: dict[str, Any],
    ids: list[str],
) -> tuple[list[PublicationEvidence], list[EvidenceSource]]:
    result = payload.get("result", {})
    retrieved_at = datetime.now(UTC)
    publications: list[PublicationEvidence] = []
    sources: list[EvidenceSource] = []
    for pmid in ids:
        item = result.get(pmid)
        if not isinstance(item, dict):
            continue
        source_id = f"PUBMED:{pmid}"
        title = str(item.get("title") or f"PubMed record {pmid}").rstrip(".")
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        authors = [
            str(author.get("name"))
            for author in item.get("authors", [])
            if author.get("name")
        ]
        publications.append(
            PublicationEvidence(
                pmid=pmid,
                title=title,
                journal=item.get("fulljournalname") or item.get("source"),
                publication_date=item.get("pubdate"),
                authors=authors[:8],
                url=url,
                source_id=source_id,
            )
        )
        sources.append(
            EvidenceSource(
                source_id=source_id,
                source_type="publication",
                title=title,
                url=url,
                record_id=pmid,
                retrieved_at=retrieved_at,
                locator="PubMed document summary",
            )
        )
    return publications, sources
