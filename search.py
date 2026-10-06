from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from providers import europe_pmc, openalex


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_summary(
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


def run_provider(
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
    write_summary(output_dir, provider_slug, provider_name, query, records)

    print(f"LAIPC+ Stage {stage} - {provider_name}")
    print(f"Query: {query}")
    print(f"Results: {len(records)}")
    print("Status: OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAIPC+ Search Engine")
    parser.add_argument(
        "--provider",
        choices=["foundation", "europe_pmc", "openalex"],
        default="foundation",
    )
    parser.add_argument(
        "--query",
        default="chronic stress mice behavioral",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=25,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.provider == "foundation":
        run_foundation(output_dir)
    else:
        run_provider(args.provider, args.query, args.max_results, output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LAIPC+ execution failed: {exc}", file=sys.stderr)
        raise
