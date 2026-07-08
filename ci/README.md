# MSGCTF DevSecOps CI/CD Plan

## Role

DevSecOps makes challenge images safe, traceable, repeatable, and ready for runtime deployment.

When a challenge changes, the pipeline must leave enough evidence to answer:

- Which challenge produced this image?
- Which commit or submitted image did it come from?
- Which registry URL and digest should runtime use?
- Did secret scanning pass?
- Did vulnerability scanning pass?
- Is the result deployable or blocked?

CI/CD must not stop at build automation. In MSGCTF, an unsafe image can become a live challenge during the event. The pipeline has to prevent secret leaks, block serious vulnerabilities, preserve image provenance, and generate a deployment artifact that runtime and scheduler can consume.

## Pipeline Modes

MSGCTF can support two challenge intake modes.

### Mode A: Source Build Pipeline

Use this when challenge authors push source code to a challenge repository.

Flow:

```text
challenge repo push
-> validate challenge metadata
-> docker build
-> gitleaks scan
-> trivy scan
-> registry push
-> digest extraction
-> artifact.json generation
```

This mode is good when MSGCTF controls the repository format and wants reproducible builds from source.

### Mode B: Submitted Image Pipeline

Use this when challenge authors build their own image and submit an image reference.

Flow:

```text
challenge metadata push
-> validate challenge.toml
-> docker pull submitted image
-> gitleaks scan on metadata repo
-> trivy scan on submitted image
-> health check
-> promote approved image to MSGCTF GHCR
-> digest extraction
-> artifact.json generation
```

This mode is better when authors use many different languages and build systems. MSGCTF does not need to understand Python, Node.js, Go, PHP, Java, or native build steps. The platform only requires a runnable Docker image.

Current MVP direction: use Mode B for challenge intake, while keeping Mode A documented as a possible controlled-repo option.

## Decisions To Lock First

Before full automation, decide these rules:

- Challenge repository structure
- Docker image submission format
- Build context rules for source-build challenges
- Registry provider and naming convention
- Image tag and digest policy
- Vulnerability severity policy
- Secret injection and rotation policy
- Runtime artifact schema

The first goal is repeatability and traceability. Given the same input, the system should produce the same class of output and leave a clear artifact.

## MVP Deliverables

### 1. Challenge Image Pipeline

Required:

- GitHub Actions workflow
- Docker image pull or build
- Image tag generation
- Registry push
- Digest extraction
- Artifact generation

Current files:

- `.github/workflows/challenge-deployment.yml`
- `challenge.toml`
- `scripts/validate_challenge_spec.py`
- `scripts/generate_artifact.py`
- `scripts/render_challenge_manifest.py`

### 2. Registry Policy

Recommended registry: GHCR.

Naming convention:

```text
ghcr.io/msgctf/<challenge_id>:<commit_sha>
ghcr.io/msgctf/<challenge_id>@sha256:<digest>
```

Rules:

- Runtime must use digest references.
- `latest` can exist for humans, but runtime must not depend on it.
- Every promoted image must map to one `challenge_id`.
- Registry credentials must never be committed to the repository.

### 3. Security Scanning

Tools:

- Gitleaks for secret detection
- Trivy for image vulnerability and secret scanning

Policy:

- Critical vulnerabilities block deployment.
- High vulnerabilities should be reviewed; the team must decide whether High blocks MVP.
- Scan failures must not be marked as deployable.
- Exceptions must be explicit and auditable.

### 4. Build Metadata

Every artifact should include:

- `challenge_id`
- source repository or submitted image
- commit hash
- build time
- registry URL
- image digest
- scan result
- resource profile
- container port
- health path

Example:

```json
{
  "schema_version": "1.0",
  "challenge_id": "web100",
  "submitted_image": "ghcr.io/author/web100:v1",
  "image": "ghcr.io/msgctf/web100",
  "digest": "sha256:abcd...",
  "image_ref": "ghcr.io/msgctf/web100@sha256:abcd...",
  "scan_result": "PASS",
  "resource_profile": "small",
  "container_port": 5000,
  "health_path": "/health"
}
```

### 5. Secret Management

Rules:

- Do not pass long-lived secrets through Docker build args.
- Do not leave secrets in image layers.
- Do not print secrets in CI logs.
- Separate registry credentials, cloud credentials, and challenge runtime secrets.
- Rotate registry tokens and cloud credentials before the event.
- Challenge runtime secrets should be injected at runtime through Kubernetes secrets or an external secret manager.

### 6. Runtime Artifact

Runtime and scheduler should receive an artifact, not guess from tags.

Required fields:

- `challenge_id`
- `image_ref`
- `digest`
- `resource_profile`
- `container_port`
- `health_path`
- `scan_result`

Runtime must schedule the challenge from the digest-based reference.

## Monthly Plan

### Month 1

Goal: prove image build or image promotion works end to end.

Tasks:

- Create sample challenge image pipeline.
- Push image to GHCR as a PoC.
- Record image digest.
- Document Dockerfile rules for source-build challenges.
- Document rules that prevent secrets from entering image layers.

Done when:

- One sample challenge becomes an image through CI.
- The result records commit, challenge ID, and image digest.
- Runtime can reference the image by digest.

### Month 2

Goal: add baseline security and runtime-facing artifact.

Tasks:

- Automate challenge image handling per challenge.
- Add vulnerability scanning.
- Add Dockerfile lint or policy checks for source-build challenges.
- Define registry credential management.
- Finalize deployment artifact format for runtime and scheduler.

Policy:

- A critical vulnerability must not silently pass.
- If an exception is needed, an operator approval record must remain.

### Month 3

Goal: harden registry, runtime access, and operations.

Tasks:

- Document provider and cluster registry access.
- Define image pull failure detection.
- Define retry behavior for image pull failures.
- Plan secret rotation and registry token expiry handling.
- Record image provenance.
- Write rollback criteria.

### Month 4

Goal: rehearse competition operations.

Tasks:

- Rebuild or re-promote all challenge images.
- Review vulnerability scan results.
- Test registry outage fallback.
- Define event-day image freeze procedure.
- Define post-event image and secret cleanup.

## Cross-Team Alignment

Runtime:

- Agree on digest-based image references.
- Agree on pull secret handling.
- Agree on pod security policy.

Platform/API:

- Agree on `challenge_id`.
- Agree on challenge metadata format.
- Agree on how image version and status are displayed.

Monitoring:

- Alert on image pull failures.
- Alert on registry access failures.
- Alert on failed challenge health checks.

Security:

- Agree on Dockerfile baseline.
- Agree on Trivy severity threshold.
- Agree on exception process.
- Agree on secret handling rules.

## Do Not Do

- Do not depend on mutable `latest` tags for runtime deployment.
- Do not put secrets in the repository.
- Do not put secrets in Docker image layers.
- Do not print secrets in CI logs.
- Do not ignore scan failures.
- Do not pass an image with unknown provenance to runtime.
- Do not let CI directly perform runtime scheduling.

CI produces a deployable artifact. Runtime and scheduler decide when and where it runs.

## Meeting Summary

DevSecOps owns the path from challenge input to deployable artifact.

For MVP, the pipeline should:

1. Validate challenge metadata.
2. Build or pull a challenge image depending on intake mode.
3. Scan for secrets and vulnerabilities.
4. Push or promote the approved image to GHCR.
5. Extract the immutable digest.
6. Generate `artifact.json`.
7. Hand the artifact to runtime and scheduler.

MVP is complete when a sample challenge repository update creates a scanned image and a digest-based artifact that runtime and scheduler can use.
