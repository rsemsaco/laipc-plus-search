from __future__ import annotations

from typing import Any

from .dedup import normalize_title


def _text(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(key) or "")
        for key in ("title", "abstract", "resource_type", "publication_type")
    ).lower()


def _term_hits(text: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    normalized_text = normalize_title(text) or ""
    for term in terms:
        normalized_term = normalize_title(term) or ""
        if normalized_term and normalized_term in normalized_text:
            hits.append(term)
    return sorted(set(hits))


def assign_retrieval_priority(
    records: list[dict[str, Any]],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    behavior_terms = [
        str(term)
        for term in profile.get("behavior_terms") or []
        if str(term).lower() not in {"behavioral battery", "multidimensional behavior"}
    ]
    stress_models = [str(term) for term in profile.get("stress_models") or []]

    for record in records:
        score = 0
        reasons: list[str] = []
        families = set(record.get("query_families") or [])
        text = _text(record)

        behavior_hits = _term_hits(text, behavior_terms)
        stress_hits = _term_hits(text, stress_models)

        if record.get("record_kind") == "dataset":
            score += 2
            reasons.append("dataset record")

        if record.get("has_data_signal"):
            score += 2
            reasons.append("data signal")

        if record.get("has_supplement"):
            score += 1
            reasons.append("supplement available")

        if record.get("is_open_access") or record.get("has_fulltext") or record.get("has_pdf"):
            score += 1
            reasons.append("accessible full text/open access signal")

        if "multidimensional_signal" in families:
            score += 2
            reasons.append("retrieved by multidimensional query")

        if "dataset_first" in families:
            score += 2
            reasons.append("retrieved by dataset-first query")

        if len(families) >= 2:
            score += 1
            reasons.append("found by multiple query families")
        if len(families) >= 3:
            score += 1

        hit_count = int(record.get("hit_count") or 0)
        if hit_count >= 3:
            score += 1
            reasons.append("repeated retrieval")
        if hit_count >= 5:
            score += 1

        if len(behavior_hits) >= 3:
            score += 3
            reasons.append("3+ behavioral assay terms")
        elif len(behavior_hits) == 2:
            score += 2
            reasons.append("2 behavioral assay terms")
        elif len(behavior_hits) == 1:
            score += 1
            reasons.append("1 behavioral assay term")

        if stress_hits:
            score += 1
            reasons.append("named chronic-stress model term")

        if record.get("corpus_status") == "RELATED_TO_KNOWN":
            score += 2
            reasons.append("dataset/resource linked to known article")

        if score >= 8:
            label = "Alta"
        elif score >= 4:
            label = "Media"
        else:
            label = "Exploratoria"

        record["retrieval_priority_score"] = score
        record["retrieval_priority"] = label
        record["priority_reasons"] = reasons
        record["behavior_term_hits"] = behavior_hits
        record["stress_model_hits"] = stress_hits

    records.sort(
        key=lambda r: (
            {"Alta": 0, "Media": 1, "Exploratoria": 2}.get(
                str(r.get("retrieval_priority")), 9
            ),
            0 if r.get("corpus_status") == "NEW" else 1,
            -int(r.get("retrieval_priority_score") or 0),
            -(int(r.get("year")) if str(r.get("year") or "").isdigit() else 0),
            str(r.get("title") or "").lower(),
        )
    )
    return records
