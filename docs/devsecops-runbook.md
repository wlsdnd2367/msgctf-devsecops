# MSGCTF DevSecOps Runbook

## Pipeline 1: Challenge Deployment

Owner: DevSecOps.

Responsibilities:

1. Require `challenge.toml`.
2. Validate `challenge.id`, `deployment.resource_profile`, and `monitoring.health_path`.
3. Pull the Docker image submitted by the challenge author, or build from source if the team chooses source-build mode for that challenge.
4. Run Gitleaks and fail on leaks.
5. Run Trivy and fail on critical vulnerabilities.
6. Run the image and check the declared health endpoint.
7. Promote the approved image to MSGCTF GHCR.
8. Extract the promoted image digest.
9. Generate `artifact.json`.
10. Upload the artifact for the MSGCTF runtime.

The runtime must deploy by digest, not by mutable tag.

## Pipeline 2: Platform CI/CD

Owner: Platform plus DevSecOps.

Responsibilities:

1. Run component tests.
2. Build frontend, backend, runtime, and scheduler images.
3. Run Gitleaks.
4. Run Trivy.
5. Push component images to GHCR.
6. Authenticate to GCP through Workload Identity Federation.
7. Deploy manifests to GKE.

## Runtime Contract

Backend owns challenge metadata:

```json
{
  "challenge_id": "web100",
  "tile_id": 12,
  "resource_profile": "small"
}
```

Runtime consumes `artifact.json`:

```json
{
  "challenge_id": "web100",
  "digest": "sha256:abcd",
  "resource_profile": "small",
  "container_port": 5000,
  "health_path": "/health"
}
```

Scheduler maps resource profiles:

```json
{
  "small": {
    "requests": {"cpu": "250m", "memory": "256Mi"},
    "limits": {"cpu": "500m", "memory": "512Mi"}
  }
}
```

Kubernetes runs the final challenge pod in the `challenge` namespace.
