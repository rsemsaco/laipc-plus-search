from __future__ import annotations

import os
import time
from typing import Any

import requests


BASE_URL = "https://api.openalex.org/works"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


def _strip_openalex_doi(value: Any) -> str | None:
    if not value:
        return None
    doi = str(value).strip()
    prefix = "https://doi.org/"
    if doi.lower().startswith(prefix):
        return doi[len(prefix):]
    return doi


def _authors(item: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for authorship in item.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            names.append(str(name))
    return names


def _abstract_from_inverted_index(index: Any) -> str | None:
    if not isinstance(index, dict) or not index:
        return None

    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                positioned.append((position, str(word)))

    if not positioned:
        return None

    positioned.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned)


def _best_article_url(item: dict[str, Any], doi: str | None) -> str | None:
    best_oa = item.get("best_oa_location") or {}
    primary = item.get("primary_location") or {}

    for candidate in (
        best_oa.get("landing_page_url"),
        best_oa.get("pdf_url"),
        primary.get("landing_page_url"),
        primary.get("pdf_url"),
    ):
        if candidate:
            return str(candidate)

    if doi:
        return f"https://doi.org/{doi}"

    openalex_id = item.get("id")
    return str(openalex_id) if openalex_id else None


def _request(params: dict[str, Any]) -> requests.Response:
    headers = {
        "User-Agent": "LAIPC-Plus-Search/0.1",
        "Accept": "application/json",
    }

    api_key = os.getenv("OPENALEX_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                BASE_URL,
                params=params,
                headers=headers,
                timeout=TIMEOUT_SECONDS,
            )

            if response.status_code == 429 or response.status_code >= 500:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue

            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("OpenAlex request failed without a captured exception")


def search(query: str, max_results: int = 25) -> list[dict[str, Any]]:
    """Search scholarly works in OpenAlex.

    OpenAlex permits basic keyless queries. If OPENALEX_API_KEY is present in
    the environment it is used automatically, allowing a larger free budget.
    """
    per_page = max(1, min(int(max_results), 100))

    response = _request(
        {
            "search": query,
            "per_page": per_page,
        }
    )
    payload = response.json()
    results = payload.get("results") or []

    records: list[dict[str, Any]] = []
    for item in results[:per_page]:
        doi = _strip_openalex_doi(item.get("doi"))
        primary = item.get("primary_location") or {}
        source = primary.get("source") or {}
        best_oa = item.get("best_oa_location") or {}
        open_access = item.get("open_access") or {}
        ids = item.get("ids") or {}

        records.append(
            {
                "source": "OpenAlex",
                "source_id": item.get("id"),
                "title": item.get("display_name") or item.get("title"),
                "authors": _authors(item),
                "year": item.get("publication_year"),
                "journal": source.get("display_name"),
                "doi": doi,
                "pmid": ids.get("pmid"),
                "pmcid": ids.get("pmcid"),
                "abstract": _abstract_from_inverted_index(
                    item.get("abstract_inverted_index")
                ),
                "publication_type": item.get("type"),
                "is_open_access": bool(open_access.get("is_oa")),
                "oa_status": open_access.get("oa_status"),
                "has_pdf": bool(best_oa.get("pdf_url") or primary.get("pdf_url")),
                "has_fulltext": bool(item.get("has_fulltext")),
                "cited_by_count": item.get("cited_by_count"),
                "article_url": _best_article_url(item, doi),
            }
        )

    return records
