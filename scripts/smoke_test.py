from __future__ import annotations

import argparse
import json
import sys

import httpx


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the AI Intelligence Hub backend.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--expect-data", action="store_true", help="Require at least one issue and one rag chunk")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        with httpx.Client(timeout=20) as client:
            health = client.get(f"{base_url}/health")
            require(health.status_code == 200, f"/health failed: {health.status_code}")

            health_details = client.get(f"{base_url}/health/details")
            require(health_details.status_code == 200, f"/health/details failed: {health_details.status_code}")
            details_payload = health_details.json()

            issues = client.get(f"{base_url}/issues")
            require(issues.status_code == 200, f"/issues failed: {issues.status_code}")
            issues_payload = issues.json()

            digest = client.get(f"{base_url}/daily-digest")
            require(digest.status_code == 200, f"/daily-digest failed: {digest.status_code}")
            digest_payload = digest.json()
    except httpx.HTTPError as exc:
        raise SystemExit(f"Smoke test could not reach backend at {base_url}: {exc}") from exc

    if args.expect_data:
        require(details_payload["feed"]["issue_count"] > 0, "Expected issue data, but issue_count is 0")
        require(details_payload["rag"]["total_chunks"] > 0, "Expected RAG chunks, but total_chunks is 0")
        require(bool(digest_payload.get("issue")), "Expected latest issue payload, but /daily-digest returned no issue")

    summary = {
        "health": health.json(),
        "issue_count": details_payload["feed"]["issue_count"],
        "content_item_count": details_payload["feed"]["content_item_count"],
        "rag_chunks": details_payload["rag"]["total_chunks"],
        "latest_issue_date": details_payload["feed"]["latest_issue_date"],
        "last_daily_digest_run": details_payload["scheduler"]["last_daily_digest_run"],
    }
    json.dump(summary, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
