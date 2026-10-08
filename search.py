from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from engine.protocol_runner import run_protocol
from engine.query_builder import build_query_plan, load_profile
from engine.stage4 import process_stage4, write_csv
from providers import datacite, europe_pmc, openalex


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_provider_summary(
    output_dir: Path,
    provider_slug: str,
    provider_name: str,
    query: str,
    records: list[dict],
) -> None:
    summary_lines = [
        f"# LAIPC+ {provider_name} test",
        "",
        f"- Query: {query}",
        f"- Results returned: {len(records)}",
        "",
        "## First results",
    ]
    for index, record in enumerate(records[:10], start=1):
        title = record.get("title") or "(untitled)"
        doi = record.get("doi") or "no DOI"
        summary_lines.append(f"{index}. {title} | {doi}")

    (output_dir / f"{provider_slug}_summary.md").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )


def run_foundation(output_dir: Path) -> None:
    payload = {
        "app": "LAIPC+ Search Engine",
        "version": "0.1-foundation",
        "environment": "GitHub Actions" if os.getenv("GITHUB_ACTIONS") == "true" else "local/other",
        "status": "OK",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "workflow_run_id": os.getenv("GITHUB_RUN_ID"),
    }
    write_json(output_dir / "execution_test.json", payload)
    print("LAIPC+ Search Engine v0.1")
    print(f"Environment: {payload['environment']}")
    print("Status: OK")


def run_single_provider(
    provider_slug: str,
    query: str,
    max_results: int,
    output_dir: Path,
) -> None:
    if provider_slug == "europe_pmc":
        provider_name = "Europe PMC"
        records = europe_pmc.search(query=query, max_results=max_results)
        stage = "2.1"
    elif provider_slug == "openalex":
        provider_name = "OpenAlex"
        records = openalex.search(query=query, max_results=max_results)
        stage = "2.2"
    elif provider_slug == "datacite":
        provider_name = "DataCite"
        records = datacite.search(query=query, max_results=max_results)
        stage = "2.3"
    else:
        raise ValueError(f"Unsupported provider: {provider_slug}")

    payload = {
        "app": "LAIPC+ Search Engine",
        "stage": stage,
        "provider": provider_name,
        "query": query,
        "requested_max_results": max_results,
        "returned_results": len(records),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }

    write_json(output_dir / f"{provider_slug}_results.json", payload)
    write_provider_summary(output_dir, provider_slug, provider_name, query, records)

    print(f"LAIPC+ Stage {stage} - {provider_name}")
    print(f"Query: {query}")
    print(f"Results: {len(records)}")
    print("Status: OK")


def write_query_plan(output_dir: Path, profile: dict, plan: list) -> None:
    plan_payload = {
        "profile_id": profile.get("profile_id"),
        "research_question": profile.get("research_question"),
        "query_count": len(plan),
        "queries": [item.to_dict() for item in plan],
    }
    write_json(output_dir / "query_plan.json", plan_payload)

    lines = [
        "# LAIPC+ Stage 3 query plan",
        "",
        f"- Profile: {profile.get('profile_id')}",
        f"- Queries: {len(plan)}",
        "",
        "| ID | Family | Query |",
        "|---|---|---|",
    ]
    for item in plan:
        lines.append(f"| {item.query_id} | {item.family} | {item.query} |")

    (output_dir / "query_plan.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def write_protocol_summary(
    output_dir: Path,
    profile: dict,
    plan: list,
    run: dict,
) -> None:
    lines = [
        "# LAIPC+ Stage 3 protocol search",
        "",
        f"- Profile: {profile.get('profile_id')}",
        f"- Queries generated: {len(plan)}",
        f"- Providers: {', '.join(run['providers'])}",
        f"- Provider-query calls: {run['provider_query_calls']}",
        f"- Raw records retrieved: {run['raw_record_count']}",
        f"- Errors: {len(run['errors'])}",
        "",
        "## Counts by provider",
    ]

    for provider, count in run["counts_by_provider"].items():
        lines.append(f"- {provider}: {count}")

    lines.extend(["", "## Counts by query family"])
    for family, count in run["counts_by_family"].items():
        lines.append(f"- {family}: {count}")

    if run["errors"]:
        lines.extend(["", "## Retrieval errors"])
        for error in run["errors"]:
            lines.append(
                f"- {error['query_id']} / {error['provider']}: "
                f"{error['error_type']} - {error['error']}"
            )

    lines.extend([
        "",
        "## Important",
        "This is a raw retrieval package. Duplicate records are intentionally retained.",
        "KNOWN/NEW comparison, deduplication and prioritization belong to Stage 4.",
    ])

    (output_dir / "protocol_run_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def execute_protocol(
    profile_path: str,
    max_results_per_query: int,
    output_dir: Path,
) -> tuple[dict, list, dict]:
    profile = load_profile(profile_path)
    plan = build_query_plan(profile)
    write_query_plan(output_dir, profile, plan)

    run = run_protocol(
        query_plan=plan,
        provider_slugs=["europe_pmc", "openalex", "datacite"],
        max_results_per_query=max_results_per_query,
    )
    return profile, plan, run


def run_research_protocol(
    profile_path: str,
    max_results_per_query: int,
    output_dir: Path,
) -> None:
    profile, plan, run = execute_protocol(profile_path, max_results_per_query, output_dir)

    payload = {
        "app": "LAIPC+ Search Engine",
        "stage": "3",
        "profile_id": profile.get("profile_id"),
        "research_question": profile.get("research_question"),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        **run,
    }
    write_json(output_dir / "protocol_raw_results.json", payload)
    write_protocol_summary(output_dir, profile, plan, run)

    print("LAIPC+ Stage 3 - Protocol-oriented search")
    print(f"Profile: {profile.get('profile_id')}")
    print(f"Queries: {len(plan)}")
    print(f"Provider-query calls: {run['provider_query_calls']}")
    print(f"Raw records: {run['raw_record_count']}")
    print(f"Errors: {len(run['errors'])}")
    print("Status: OK")


def write_stage4_summary(output_dir: Path, audit: dict) -> None:
    status_counts = audit.get("status_counts") or {}
    priority_counts = audit.get("priority_counts") or {}

    lines = [
        "# LAIPC+ Stage 4 - Deduplication + corpus comparison",
        "",
        f"- Raw records: {audit['raw_record_count']}",
        f"- Unique records: {audit['unique_record_count']}",
        f"- Duplicates removed: {audit['duplicates_removed']}",
        f"- Unique articles: {audit['article_count']}",
        f"- Unique datasets: {audit['dataset_count']}",
        f"- Known corpus size: {audit['known_corpus_count']}",
        "",
        "## Corpus status",
        f"- KNOWN: {status_counts.get('KNOWN', 0)}",
        f"- RELATED_TO_KNOWN: {status_counts.get('RELATED_TO_KNOWN', 0)}",
        f"- NEW: {status_counts.get('NEW', 0)}",
        "",
        "## Retrieval priority",
        f"- Alta: {priority_counts.get('Alta', 0)}",
        f"- Media: {priority_counts.get('Media', 0)}",
        f"- Exploratoria: {priority_counts.get('Exploratoria', 0)}",
        f"- NEW + Alta: {audit.get('high_priority_new_count', 0)}",
        "",
        "## Methodological boundary",
        "Retrieval priority is only a search heuristic.",
        "It does not assign S0-S3 or D0-D4 to new records.",
        "Existing S/D values appear only when a record matches the audited C01-C45 corpus.",
    ]

    (output_dir / "stage4_summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def run_stage4(
    profile_path: str,
    known_corpus_path: str,
    max_results_per_query: int,
    output_dir: Path,
) -> None:
    profile, plan, run = execute_protocol(profile_path, max_results_per_query, output_dir)

    raw_payload = {
        "app": "LAIPC+ Search Engine",
        "stage": "3",
        "profile_id": profile.get("profile_id"),
        "research_question": profile.get("research_question"),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        **run,
    }
    write_json(output_dir / "protocol_raw_results.json", raw_payload)

    ranked, audit = process_stage4(
        raw_records=run["records"],
        known_corpus_path=known_corpus_path,
        profile=profile,
    )

    stage4_payload = {
        "app": "LAIPC+ Search Engine",
        "stage": "4",
        "profile_id": profile.get("profile_id"),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit": audit,
        "records": ranked,
    }
    write_json(output_dir / "stage4_unique_records.json", stage4_payload)
    write_json(output_dir / "stage4_dedup_audit.json", audit)
    write_csv(output_dir / "stage4_all_unique.csv", ranked)

    candidate_records = [
        record
        for record in ranked
        if record.get("corpus_status") in {"NEW", "RELATED_TO_KNOWN"}
    ]
    write_csv(output_dir / "stage4_new_candidates.csv", candidate_records)
    write_stage4_summary(output_dir, audit)

    print("LAIPC+ Stage 4 - Deduplication + KNOWN/NEW")
    print(f"Raw records: {audit['raw_record_count']}")
    print(f"Unique records: {audit['unique_record_count']}")
    print(f"Duplicates removed: {audit['duplicates_removed']}")
    print(f"KNOWN: {audit['status_counts'].get('KNOWN', 0)}")
    print(f"RELATED_TO_KNOWN: {audit['status_counts'].get('RELATED_TO_KNOWN', 0)}")
    print(f"NEW: {audit['status_counts'].get('NEW', 0)}")
    print(f"NEW + Alta: {audit['high_priority_new_count']}")
    print("Status: OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAIPC+ Search Engine")
    parser.add_argument(
        "--mode",
        choices=["foundation", "provider_test", "protocol", "stage4"],
        default="foundation",
    )
    parser.add_argument(
        "--provider",
        choices=["europe_pmc", "openalex", "datacite"],
        default="europe_pmc",
    )
    parser.add_argument(
        "--query",
        default="chronic stress mice behavioral",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--profile",
        default="config/research_profile.yaml",
    )
    parser.add_argument(
        "--known-corpus",
        default="reference/corpus_known.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "foundation":
        run_foundation(output_dir)
    elif args.mode == "provider_test":
        run_single_provider(args.provider, args.query, args.max_results, output_dir)
    elif args.mode == "protocol":
        run_research_protocol(args.profile, args.max_results, output_dir)
    elif args.mode == "stage4":
        run_stage4(args.profile, args.known_corpus, args.max_results, output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LAIPC+ execution failed: {exc}", file=sys.stderr)
        raise
