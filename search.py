from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from providers import europe_pmc


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


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


def run_europe_pmc(query: str, max_results: int, output_dir: Path) -> None:
    records = europe_pmc.search(query=query, max_results=max_results)
    payload = {
        "app": "LAIPC+ Search Engine",
        "stage": "2.1",
        "provider": "Europe PMC",
        "query": query,
        "requested_max_results": max_results,
        "returned_results": len(records),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "records": records,
    }
    write_json(output_dir / "europe_pmc_results.json", payload)

    summary_lines = [
        "# LAIPC+ Europe PMC test",
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

    (output_dir / "europe_pmc_summary.md").write_text(
        "\n".join(summary_lines) + "\n",
        encoding="utf-8",
    )

    print("LAIPC+ Stage 2.1 - Europe PMC")
    print(f"Query: {query}")
    print(f"Results: {len(records)}")
    print("Status: OK")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAIPC+ Search Engine")
    parser.add_argument(
        "--provider",
        choices=["foundation", "europe_pmc"],
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
    elif args.provider == "europe_pmc":
        run_europe_pmc(args.query, args.max_results, output_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LAIPC+ execution failed: {exc}", file=sys.stderr)
        raise
