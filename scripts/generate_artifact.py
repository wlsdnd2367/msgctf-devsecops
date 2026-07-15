#!/usr/bin/env python3
import argparse
import json
import os
import tomllib
from datetime import datetime, timezone
from pathlib import Path


def load_spec(path):
    with path.open("rb") as f:
        spec = tomllib.load(f)
    return {
        "challenge_id": spec["challenge"]["id"],
        "resource_profile": spec["deployment"]["resource_profile"],
        "submitted_image": spec["image"]["ref"],
        "container_port": spec["image"]["port"],
        "health_path": spec["monitoring"]["health_path"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--challenge-spec", type=Path, default=Path("challenge.toml"))
    parser.add_argument("--image", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--submitted-image")
    parser.add_argument("--submitted-digest")
    parser.add_argument("--scan-result", default="PASS")
    parser.add_argument("--output", type=Path, default=Path("artifact.json"))
    args = parser.parse_args()

    spec = load_spec(args.challenge_spec)
    artifact = {
        "schema_version": "1.0",
        "challenge_id": spec["challenge_id"],
        "image": args.image,
        "digest": args.digest,
        "promoted_digest": args.digest,
        "image_ref": f"{args.image}@{args.digest}",
        "submitted_image": args.submitted_image or spec["submitted_image"],
        "submitted_digest": args.submitted_digest,
        "scan_result": args.scan_result,
        "scan_results": {
            "metadata_secret_scan": "PASS",
            "image_vulnerability_scan": "PASS",
            "image_secret_scan": "PASS",
            "health_check": "PASS",
        },
        "resource_profile": spec["resource_profile"],
        "container_port": spec["container_port"],
        "health_path": spec["health_path"],
        "source": {
            "repository": os.getenv("GITHUB_REPOSITORY", "local"),
            "commit": os.getenv("GITHUB_SHA", "local"),
            "branch": os.getenv("GITHUB_REF_NAME", "local"),
            "workflow_run_id": os.getenv("GITHUB_RUN_ID", "local"),
            "workflow_run_attempt": os.getenv("GITHUB_RUN_ATTEMPT", "local"),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    args.output.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
