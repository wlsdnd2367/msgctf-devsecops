# MSGCTF DevSecOps

MSGCTF uses two CI/CD pipelines:

- Challenge Deployment Pipeline: validates challenge metadata, pulls the author-submitted Docker image, blocks secrets and critical vulnerabilities, promotes the approved image to MSGCTF GHCR, and emits an artifact for the runtime.
- Platform Pipeline: tests and ships the platform components to GKE.

## Challenge Repo Contract

Every challenge submission repo must include:

```text
challenge.toml
```

Required `challenge.toml` fields:

```toml
[challenge]
id = "web100"

[deployment]
resource_profile = "small"

[image]
ref = "ghcr.io/author/web100:2026-07-01"
port = 5000

[monitoring]
health_path = "/health"
```

Validate locally:

```bash
python3 scripts/validate_challenge_spec.py challenge.toml
```

The submitted image can be built in any language. MSGCTF only requires a runnable Docker image with the declared health endpoint.

Check an image locally:

```bash
colima start
docker pull ghcr.io/author/web100:2026-07-01
docker run --rm -p 5050:5000 ghcr.io/author/web100:2026-07-01
curl http://127.0.0.1:5050/health
```

## GitHub Actions

- `.github/workflows/challenge-deployment.yml`: submitted image pull, scan, health check, GHCR promotion, artifact generation.
- `.github/workflows/platform-cicd.yml`: platform tests, image builds, scans, GHCR push, GKE deploy.
- `.github/workflows/devsecops.yml`: compatibility wrapper for this sample repo.

Required GitHub settings:

- `Settings > Actions > General > Workflow permissions`: read and write permissions.
- `packages: write` permission is defined in workflow permissions.

Required platform deployment secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `GKE_CLUSTER`
- `GKE_LOCATION`

## GKE Layout

```text
GKE
├─ platform
│  ├─ frontend
│  ├─ backend
│  ├─ runtime
│  ├─ scheduler
│  └─ monitoring
└─ challenge
   ├─ web100
   ├─ web200
   ├─ crypto100
   └─ pwn100
```

Resource profiles live in `config/resource-profiles.json`.

## Runtime Artifact

The challenge pipeline writes `artifact.json`:

```json
{
  "challenge_id": "web100",
  "image": "ghcr.io/msgctf/web100",
  "submitted_image": "ghcr.io/author/web100:2026-07-01",
  "digest": "sha256:...",
  "scan_result": "PASS",
  "resource_profile": "small",
  "container_port": 5000,
  "health_path": "/health"
}
```
