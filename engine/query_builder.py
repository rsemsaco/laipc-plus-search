from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class QuerySpec:
    query_id: str
    family: str
    query: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def load_profile(path: str | Path) -> dict[str, Any]:
    profile_path = Path(path)
    with profile_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError("Research profile must be a YAML mapping.")

    return data


def _normalize_query(text: str) -> str:
    return " ".join(str(text).split()).strip()


def build_query_plan(profile: dict[str, Any]) -> list[QuerySpec]:
    strategy = profile.get("query_strategy") or {}
    max_queries = int(strategy.get("max_queries") or 20)

    candidates: list[tuple[str, str, str]] = []

    for query in strategy.get("broad_queries") or []:
        candidates.append(
            (
                "broad_literature",
                _normalize_query(query),
                "Broad retrieval of chronic-stress rodent behavioral literature.",
            )
        )

    model_suffix = _normalize_query(strategy.get("model_suffix") or "rodent behavioral")
    for model in profile.get("stress_models") or []:
        candidates.append(
            (
                "model_specific",
                _normalize_query(f"{model} {model_suffix}"),
                f"Expands retrieval around the named stress model: {model}.",
            )
        )

    for combination in strategy.get("assay_combinations") or []:
        if not isinstance(combination, list):
            continue
        terms = [_normalize_query(term) for term in combination if _normalize_query(term)]
        if not terms:
            continue
        candidates.append(
            (
                "multidimensional_signal",
                _normalize_query("chronic stress rodent " + " ".join(terms)),
                "Looks for co-occurrence of multiple behavioral assays as a signal of a multidimensional battery.",
            )
        )

    for query in strategy.get("dataset_queries") or []:
        candidates.append(
            (
                "dataset_first",
                _normalize_query(query),
                "Looks explicitly for public or reusable behavioral data associated with chronic-stress studies.",
            )
        )

    seen: set[str] = set()
    plan: list[QuerySpec] = []

    for family, query, rationale in candidates:
        if not query:
            continue
        key = query.casefold()
        if key in seen:
            continue
        seen.add(key)
        plan.append(
            QuerySpec(
                query_id=f"Q{len(plan) + 1:02d}",
                family=family,
                query=query,
                rationale=rationale,
            )
        )
        if len(plan) >= max_queries:
            break

    if not plan:
        raise ValueError("Research profile generated zero queries.")

    return plan
