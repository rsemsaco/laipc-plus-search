from __future__ import annotations

import time
from typing import Any

import requests


BASE_URL = "https://api.datacite.org/dois"
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3


def _first_title(attributes: dict[str, Any]) -> str | None:
    for item in attributes.get("titles") or []:
        if isinstance(item, dict) and item.get("title"):
            return str(item["title"])
    return None


def _creator_names(attributes: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for creator in attributes.get("creators") or []:
        if not isinstance(creator, dict):
            continue
        name = creator.get("name")
        if not name:
            given = creator.get("givenName")
            family = creator.get("familyName")
            if given or family:
                name = " ".join(part for part in [given, family] if part)
        if name:
            names.append(str(name))
    return names


def _description(attributes: dict[str, Any]) -> str | None:
    descriptions = attributes.get("descriptions") or []
    for item in descriptions:
        if not isinstance(item, dict):
            continue
        if item.get("descriptionType") == "Abstract" and item.get("description"):
            return str(item["description"])
    for item in descriptions:
        if isinstance(item, dict) and item.get("description"):
            return str(item["description"])
    return None


def _related_identifiers(attributes: dict[str, Any]) -> list[dict[str, Any]]:
    related: list[dict[str, Any]] = []
    for item in attributes.get("relatedIdentifiers") or []:
        if not isinstance(item, dict):
            continue
        identifier = item.get("relatedIdentifier")
        if not identifier:
            continue
        related.append(
            {
                "identifier": identifier,
                "identifier_type": item.get("relatedIdentifierType"),
                "relation_type": item.get("relationType"),
                "resource_type_general": item.get("resourceTypeGeneral"),
            }
        )
    return related


def _rights(attributes: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in attributes.get("rightsList") or []:
        if not isinstance(item, dict):
            continue
        output.append(
            {
                "rights": item.get("rights"),
                "rights_uri": item.get("rightsUri"),
                "rights_identifier": item.get("rightsIdentifier"),
            }
        )
    return output


def _subjects(attributes: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for item in attributes.get("subjects") or []:
        if isinstance(item, dict) and item.get("subject"):
            values.append(str(item["subject"]))
    return values


def _request(params: dict[str, Any]) -> requests.Response:
    headers = {
        "User-Agent": "LAIPC-Plus-Search/0.1",
        "Accept": "application/vnd.api+json",
    }

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
    raise RuntimeError("DataCite request failed without a captured exception")


def search(query: str, max_results: int = 25) -> list[dict[str, Any]]:
    """Search DataCite for dataset DOI metadata.

    Stage 2.3 intentionally filters to resourceTypeGeneral=Dataset because the
    current LAIPC+ use case is dataset-first discovery. No scientific eligibility
    decision is made here.
    """
    page_size = max(1, min(int(max_results), 100))

    response = _request(
        {
            "query": query,
            "resource-type-id": "dataset",
            "page[size]": page_size,
            "sort": "relevance",
        }
    )
    payload = response.json()

    records: list[dict[str, Any]] = []
    for item in payload.get("data") or []:
        attributes = item.get("attributes") or {}
        doi = attributes.get("doi") or item.get("id")
        types = attributes.get("types") or {}
        url = attributes.get("url")

        records.append(
            {
                "source": "DataCite",
                "source_id": item.get("id"),
                "title": _first_title(attributes),
                "authors": _creator_names(attributes),
                "year": attributes.get("publicationYear"),
                "publisher": attributes.get("publisher"),
                "doi": doi,
                "abstract": _description(attributes),
                "publication_type": types.get("resourceTypeGeneral"),
                "resource_type": types.get("resourceType"),
                "dataset_url": url or (f"https://doi.org/{doi}" if doi else None),
                "subjects": _subjects(attributes),
                "rights": _rights(attributes),
                "related_identifiers": _related_identifiers(attributes),
                "created": attributes.get("created"),
                "published": attributes.get("published"),
                "registered": attributes.get("registered"),
                "state": attributes.get("state"),
            }
        )

    return records
