from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from .corpus import annotate_known_status, load_known_corpus
from .dedup import deduplicate
from .prioritize import assign_retrieval_priority


CSV_FIELDS = [
    "record_kind",
    "corpus_status",
    "known_id",
    "known_scientific_fit",
    "known_data_reuse",
    "known_prior_priority",
    "retrieval_priority",
    "retrieval_priority_score",
    "title",
    "year",
    "authors",
    "journal",
    "publisher",
    "doi",
    "pmid",
    "pmcid",
    "article_url",
    "dataset_url",
    "sources",
    "hit_count",
    "query_ids",
    "query_families",
    "has_data_signal",
    "has_supplement",
    "is_open_access",
    "has_fulltext",
    "has_pdf",
    "behavior_term_hits",
    "stress_model_hits",
    "priority_reasons",
    "corpus_match_method",
]


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return value


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: _csv_value(record.get(key)) for key in CSV_FIELDS})


def process_stage4(
    raw_records: list[dict[str, Any]],
    known_corpus_path: str | Path,
    profile: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    unique, dedup_audit = deduplicate(raw_records)
    corpus = load_known_corpus(known_corpus_path)
    annotated = annotate_known_status(unique, corpus)
    ranked = assign_retrieval_priority(annotated, profile)

    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    for record in ranked:
        status = str(record.get("corpus_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        priority = str(record.get("retrieval_priority") or "UNKNOWN")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    audit = {
        **dedup_audit,
        "known_corpus_count": len(corpus),
        "status_counts": status_counts,
        "priority_counts": priority_counts,
        "high_priority_new_count": sum(
            1
            for record in ranked
            if record.get("corpus_status") == "NEW"
            and record.get("retrieval_priority") == "Alta"
        ),
        "related_to_known_count": sum(
            1 for record in ranked if record.get("corpus_status") == "RELATED_TO_KNOWN"
        ),
    }
    return ranked, audit
