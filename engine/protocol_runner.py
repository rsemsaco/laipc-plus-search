from __future__ import annotations

import time
from collections import Counter
from typing import Any, Callable

from providers import datacite, europe_pmc, openalex

from .query_builder import QuerySpec


ProviderSearch = Callable[[str, int], list[dict[str, Any]]]

PROVIDERS: dict[str, tuple[str, ProviderSearch]] = {
    "europe_pmc": ("Europe PMC", europe_pmc.search),
    "openalex": ("OpenAlex", openalex.search),
    "datacite": ("DataCite", datacite.search),
}


def run_protocol(
    query_plan: list[QuerySpec],
    provider_slugs: list[str],
    max_results_per_query: int,
    pause_seconds: float = 0.15,
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts_by_provider: Counter[str] = Counter()
    counts_by_family: Counter[str] = Counter()
    counts_by_query: Counter[str] = Counter()

    unknown = [slug for slug in provider_slugs if slug not in PROVIDERS]
    if unknown:
        raise ValueError(f"Unsupported providers: {', '.join(unknown)}")

    for query_spec in query_plan:
        for provider_slug in provider_slugs:
            provider_name, provider_search = PROVIDERS[provider_slug]
            try:
                records = provider_search(
                    query=query_spec.query,
                    max_results=max_results_per_query,
                )
            except Exception as exc:
                errors.append(
                    {
                        "query_id": query_spec.query_id,
                        "family": query_spec.family,
                        "query": query_spec.query,
                        "provider": provider_name,
                        "provider_slug": provider_slug,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue

            counts_by_provider[provider_name] += len(records)
            counts_by_family[query_spec.family] += len(records)
            counts_by_query[query_spec.query_id] += len(records)

            for record in records:
                enriched = dict(record)
                enriched["retrieval_query_id"] = query_spec.query_id
                enriched["retrieval_query_family"] = query_spec.family
                enriched["retrieval_query"] = query_spec.query
                enriched["retrieval_rationale"] = query_spec.rationale
                enriched["retrieval_provider_slug"] = provider_slug
                results.append(enriched)

            if pause_seconds > 0:
                time.sleep(pause_seconds)

    return {
        "providers": provider_slugs,
        "max_results_per_query": max_results_per_query,
        "query_count": len(query_plan),
        "provider_query_calls": len(query_plan) * len(provider_slugs),
        "raw_record_count": len(results),
        "counts_by_provider": dict(counts_by_provider),
        "counts_by_family": dict(counts_by_family),
        "counts_by_query": dict(counts_by_query),
        "errors": errors,
        "records": results,
    }
