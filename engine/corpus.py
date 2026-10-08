from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .dedup import normalize_doi, normalize_pmcid, normalize_pmid, normalize_title


def load_known_corpus(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        raise ValueError("Known corpus is empty.")

    return rows


def build_known_indexes(corpus: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    indexes: dict[str, dict[str, dict[str, str]]] = {
        "doi": {},
        "pmid": {},
        "pmcid": {},
        "dataset_doi": {},
        "reference_title": {},
    }

    for row in corpus:
        doi = normalize_doi(row.get("doi"))
        pmid = normalize_pmid(row.get("pmid"))
        pmcid = normalize_pmcid(row.get("pmcid"))
        dataset_doi = normalize_doi(row.get("dataset_doi"))
        reference_title = normalize_title(row.get("reference"))

        if doi:
            indexes["doi"][doi] = row
        if pmid:
            indexes["pmid"][pmid] = row
        if pmcid:
            indexes["pmcid"][pmcid] = row
        if dataset_doi:
            indexes["dataset_doi"][dataset_doi] = row
        if reference_title:
            indexes["reference_title"][reference_title] = row

    return indexes


def _match_article(record: dict[str, Any], indexes: dict[str, dict[str, dict[str, str]]]) -> tuple[dict[str, str] | None, str | None]:
    for doi in record.get("all_dois") or []:
        normalized = normalize_doi(doi)
        if normalized and normalized in indexes["doi"]:
            return indexes["doi"][normalized], "doi"

    for pmid in record.get("all_pmids") or []:
        normalized = normalize_pmid(pmid)
        if normalized and normalized in indexes["pmid"]:
            return indexes["pmid"][normalized], "pmid"

    for pmcid in record.get("all_pmcids") or []:
        normalized = normalize_pmcid(pmcid)
        if normalized and normalized in indexes["pmcid"]:
            return indexes["pmcid"][normalized], "pmcid"

    # Safe title fallback: only when the known reference actually contains the full
    # normalized article title, avoiding aggressive fuzzy corpus matching.
    title = normalize_title(record.get("title"))
    if title and len(title) >= 40:
        for ref_title, row in indexes["reference_title"].items():
            if title in ref_title:
                return row, "title_in_reference"

    return None, None


def annotate_known_status(
    records: list[dict[str, Any]],
    corpus: list[dict[str, str]],
) -> list[dict[str, Any]]:
    indexes = build_known_indexes(corpus)

    for record in records:
        matched: dict[str, str] | None = None
        match_method: str | None = None

        if record.get("record_kind") == "article":
            matched, match_method = _match_article(record, indexes)
            status = "KNOWN" if matched else "NEW"
        else:
            dataset_dois = set(record.get("all_dois") or [])
            dataset_dois.update(
                item.get("doi")
                for item in record.get("related_dois") or []
                if item.get("relation_type") in {"IsIdenticalTo", "IsVersionOf", "HasVersion"}
            )
            dataset_dois = set(filter(None, (normalize_doi(x) for x in dataset_dois)))

            for doi in dataset_dois:
                if doi in indexes["dataset_doi"]:
                    matched = indexes["dataset_doi"][doi]
                    match_method = "dataset_doi"
                    break

            if matched:
                status = "KNOWN"
            else:
                article_links = []
                for item in record.get("related_dois") or []:
                    relation = item.get("relation_type") or ""
                    if relation in {"IsIdenticalTo", "IsVersionOf", "HasVersion"}:
                        continue
                    doi = normalize_doi(item.get("doi"))
                    if doi:
                        article_links.append(doi)

                for doi in article_links:
                    if doi in indexes["doi"]:
                        matched = indexes["doi"][doi]
                        match_method = "related_article_doi"
                        break

                status = "RELATED_TO_KNOWN" if matched else "NEW"

        record["corpus_status"] = status
        record["corpus_match_method"] = match_method
        record["known_id"] = matched.get("known_id") if matched else None
        record["known_scientific_fit"] = matched.get("scientific_fit") if matched else None
        record["known_data_reuse"] = matched.get("data_reuse") if matched else None
        record["known_prior_priority"] = matched.get("prior_priority") if matched else None

    return records
