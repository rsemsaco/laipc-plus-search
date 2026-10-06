from __future__ import annotations

import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

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

    output_file = output_dir / "execution_test.json"
    output_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print("LAIPC+ Search Engine v0.1")
    print(f"Environment: {payload['environment']}")
    print("Status: OK")
    print(f"Output: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"LAIPC+ foundation test failed: {exc}", file=sys.stderr)
        raise
