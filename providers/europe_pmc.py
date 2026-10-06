from __future__ import annotations

from typing import Any

import requests


BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TIMEOUT_SECONDS = 30


def _author_names(item: dict[str, Any]) -> list[str]:
    author_list = item.get("authorList") or {}
    authors = author_list.get("author") or []
    names: list[str] = []
    for author in authors:
        name = author.get("fullName") or author.get("lastName")
        if name:
            names.append(str(name))
    return names


def search(query: str, max_results: int = 25) -> list[dict[str, Any]]:
    """Search Europe PMC and return a compact normalized record list.

    This connector intentionally performs retrieval only. Scientific eligibility
    (S0-S3 / D0-D4) is not inferred here.
    """
    page_size = max(1, min(int(max_results), 100))

    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": page_size,
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=TIMEOUT_SECONDS,
        headers={"User-Agent": "LAIPC-Plus-Search/0.1"},
    )
    response.raise_for_status()
    payload = response.json()

    result_list = (payload.get("resultList") or {}).get("result") or []
    records: list[dict[str, Any]] = []

    for item in result_list[:page_size]:
        doi = item.get("doi")
        pmid = item.get("pmid")
        pmcid = item.get("pmcid")

        article_url = None
        if pmcid:
            article_url = f"https://europepmc.org/articles/{pmcid}"
        elif pmid:
            article_url = f"https://europepmc.org/article/MED/{pmid}"
        elif doi:
            article_url = f"https://doi.org/{doi}"

        records.append(
            {
                "source": "Europe PMC",
                "source_id": item.get("id"),
                "title": item.get("title"),
                "authors": _author_names(item),
                "year": item.get("pubYear"),
                "journal": item.get("journalTitle"),
                "doi": doi,
                "pmid": pmid,
                "pmcid": pmcid,
                "abstract": item.get("abstractText"),
                "publication_type": item.get("pubType"),
                "is_open_access": item.get("isOpenAccess") == "Y",
                "in_epmc": item.get("inEPMC") == "Y",
                "in_pmc": item.get("inPMC") == "Y",
                "has_pdf": item.get("hasPDF") == "Y",
                "has_supplement": item.get("hasSuppl") == "Y",
                "has_data_signal": item.get("hasData") == "Y",
                "article_url": article_url,
            }
        )

    return records
