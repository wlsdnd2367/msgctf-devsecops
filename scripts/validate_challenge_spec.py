#!/usr/bin/env python3
import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

ALLOWED_PROFILES = {"small", "medium", "large"}
ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def validate(spec_path):
    with spec_path.open("rb") as f:
        spec = tomllib.load(f)

    challenge_id = spec.get("challenge", {}).get("id")
    resource_profile = spec.get("deployment", {}).get("resource_profile")
    image_ref = spec.get("image", {}).get("ref")
    image_port = spec.get("image", {}).get("port")
    health_path = spec.get("monitoring", {}).get("health_path")

    if not challenge_id:
        raise ValueError("challenge.id is required")
    if not ID_PATTERN.match(challenge_id):
        raise ValueError("challenge.id must be lowercase DNS-safe text")
    if not resource_profile:
        raise ValueError("deployment.resource_profile is required")
    if resource_profile not in ALLOWED_PROFILES:
        raise ValueError(f"deployment.resource_profile must be one of {sorted(ALLOWED_PROFILES)}")
    if not image_ref:
        raise ValueError("image.ref is required")
    if ":" not in image_ref and "@" not in image_ref:
        raise ValueError("image.ref must include a tag or digest")
    if not isinstance(image_port, int):
        raise ValueError("image.port is required and must be an integer")
    if image_port < 1 or image_port > 65535:
        raise ValueError("image.port must be between 1 and 65535")
    if not health_path:
        raise ValueError("monitoring.health_path is required")
    if not health_path.startswith("/"):
        raise ValueError("monitoring.health_path must start with /")

    return {
        "challenge_id": challenge_id,
        "resource_profile": resource_profile,
        "submitted_image": image_ref,
        "container_port": str(image_port),
        "health_path": health_path,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()

    try:
        result = validate(args.spec)
    except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
        return fail(str(exc))

    if args.json_output:
        args.json_output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    if args.github_output:
        with args.github_output.open("a", encoding="utf-8") as f:
            for key, value in result.items():
                f.write(f"{key}={value}\n")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
