from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Any


IDENTITY_RELATIONS = {"IsIdenticalTo", "IsVersionOf", "HasVersion"}


def normalize_doi(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip().lower()
    text = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", text, flags=re.I)
    text = re.sub(r"^doi:\s*", "", text, flags=re.I)
    match = re.search(r"10\.\d{4,9}/[^\s;,]+", text, flags=re.I)
    if not match:
        return None
    return match.group(0).rstrip(").,;").lower()


def normalize_pmid(value: Any) -> str | None:
    if not value:
        return None
    text = str(value)
    match = re.search(r"(?:pubmed\.ncbi\.nlm\.nih\.gov/)?(\d{6,9})", text, flags=re.I)
    return match.group(1) if match else None


def normalize_pmcid(value: Any) -> str | None:
    if not value:
        return None
    match = re.search(r"\bPMC\d+\b", str(value), flags=re.I)
    return match.group(0).upper() if match else None


def normalize_title(value: Any) -> str | None:
    if not value:
        return None
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = " ".join(text.split())
    return text or None


def record_kind(record: dict[str, Any]) -> str:
    publication_type = str(record.get("publication_type") or "").lower()
    resource_type = str(record.get("resource_type") or "").lower()
    if publication_type == "dataset" or resource_type == "dataset":
        return "dataset"
    if str(record.get("source") or "").lower() == "datacite":
        return "dataset"
    return "article"


def related_dois(record: dict[str, Any]) -> list[dict[str, str]]:
    values: list[dict[str, str]] = []
    for item in record.get("related_identifiers") or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("identifier_type") or "").upper() != "DOI":
            continue
        doi = normalize_doi(item.get("identifier"))
        if not doi:
            continue
        values.append(
            {
                "doi": doi,
                "relation_type": str(item.get("relation_type") or ""),
            }
        )
    return values


def _dataset_identity_key(record: dict[str, Any]) -> str:
    own_doi = normalize_doi(record.get("doi"))
    identity_dois = [own_doi] if own_doi else []

    for item in related_dois(record):
        if item["relation_type"] in IDENTITY_RELATIONS:
            identity_dois.append(item["doi"])

    identity_dois = sorted(set(identity_dois))
    if identity_dois:
        return "dataset:doi:" + identity_dois[0]

    title = normalize_title(record.get("title")) or ""
    year = str(record.get("year") or "")
    publisher = normalize_title(record.get("publisher")) or ""
    return f"dataset:title:{year}:{publisher}:{title}"


def primary_key(record: dict[str, Any]) -> str:
    kind = record_kind(record)

    if kind == "dataset":
        return _dataset_identity_key(record)

    doi = normalize_doi(record.get("doi"))
    if doi:
        return "article:doi:" + doi

    pmid = normalize_pmid(record.get("pmid"))
    if pmid:
        return "article:pmid:" + pmid

    pmcid = normalize_pmcid(record.get("pmcid"))
    if pmcid:
        return "article:pmcid:" + pmcid

    title = normalize_title(record.get("title")) or ""
    year = str(record.get("year") or "")
    return f"article:title:{year}:{title}"


def _richness(record: dict[str, Any]) -> int:
    score = 0
    for key in ("title", "abstract", "doi", "pmid", "pmcid", "journal", "article_url", "dataset_url"):
        if record.get(key):
            score += 1
    if record.get("abstract"):
        score += min(4, len(str(record["abstract"])) // 500)
    for key in ("is_open_access", "has_pdf", "has_fulltext", "has_supplement", "has_data_signal"):
        if record.get(key):
            score += 1
    return score


def _unique_strings(values: list[Any]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        output.append(text)
    return output


def _merge_group(records: list[dict[str, Any]], key: str) -> dict[str, Any]:
    base = dict(max(records, key=_richness))
    base["record_kind"] = record_kind(base)
    base["dedup_key"] = key
    base["hit_count"] = len(records)

    base["sources"] = sorted(_unique_strings([r.get("source") for r in records]))
    base["source_ids"] = _unique_strings([r.get("source_id") for r in records])
    base["query_ids"] = sorted(_unique_strings([r.get("retrieval_query_id") for r in records]))
    base["query_families"] = sorted(_unique_strings([r.get("retrieval_query_family") for r in records]))
    base["retrieval_queries"] = _unique_strings([r.get("retrieval_query") for r in records])
    base["all_dois"] = sorted(
        set(filter(None, (normalize_doi(r.get("doi")) for r in records)))
    )
    base["all_pmids"] = sorted(
        set(filter(None, (normalize_pmid(r.get("pmid")) for r in records)))
    )
    base["all_pmcids"] = sorted(
        set(filter(None, (normalize_pmcid(r.get("pmcid")) for r in records)))
    )
    base["dataset_urls"] = _unique_strings([r.get("dataset_url") for r in records])

    related: dict[tuple[str, str], dict[str, str]] = {}
    for record in records:
        for item in related_dois(record):
            related[(item["doi"], item["relation_type"])] = item
    base["related_dois"] = list(related.values())

    for flag in ("is_open_access", "has_pdf", "has_fulltext", "has_supplement", "has_data_signal"):
        base[flag] = any(bool(r.get(flag)) for r in records)

    return base


def _fuzzy_merge_title_only(records: list[dict[str, Any]], threshold: float = 0.96) -> list[dict[str, Any]]:
    identified: list[dict[str, Any]] = []
    title_only: list[dict[str, Any]] = []

    for record in records:
        if str(record.get("dedup_key") or "").startswith("article:title:"):
            title_only.append(record)
        else:
            identified.append(record)

    clusters: list[list[dict[str, Any]]] = []
    for record in title_only:
        title = normalize_title(record.get("title")) or ""
        year = str(record.get("year") or "")
        placed = False

        for cluster in clusters:
            anchor = cluster[0]
            anchor_year = str(anchor.get("year") or "")
            if year and anchor_year and year != anchor_year:
                continue
            anchor_title = normalize_title(anchor.get("title")) or ""
            if SequenceMatcher(None, title, anchor_title).ratio() >= threshold:
                cluster.append(record)
                placed = True
                break

        if not placed:
            clusters.append([record])

    merged = list(identified)
    for cluster in clusters:
        if len(cluster) == 1:
            merged.append(cluster[0])
            continue
        key = "article:fuzzy:" + (normalize_title(cluster[0].get("title")) or "")
        merged.append(_merge_group(cluster, key))

    return merged


def deduplicate(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        groups[primary_key(record)].append(record)

    first_pass = [_merge_group(group, key) for key, group in groups.items()]
    unique = _fuzzy_merge_title_only(first_pass)

    unique.sort(
        key=lambda r: (
            0 if r.get("record_kind") == "article" else 1,
            -(int(r.get("year")) if str(r.get("year") or "").isdigit() else 0),
            str(r.get("title") or "").lower(),
        )
    )

    audit = {
        "raw_record_count": len(records),
        "primary_group_count": len(groups),
        "unique_record_count": len(unique),
        "duplicates_removed": len(records) - len(unique),
        "article_count": sum(1 for r in unique if r.get("record_kind") == "article"),
        "dataset_count": sum(1 for r in unique if r.get("record_kind") == "dataset"),
        "multi_hit_groups": sum(1 for r in unique if int(r.get("hit_count") or 0) > 1),
    }
    return unique, audit
