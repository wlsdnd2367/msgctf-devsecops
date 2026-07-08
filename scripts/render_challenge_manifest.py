#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=Path("artifact.json"))
    parser.add_argument("--profiles", type=Path, default=Path("config/resource-profiles.json"))
    parser.add_argument("--output", type=Path, default=Path("dist/challenge-manifest.yaml"))
    args = parser.parse_args()

    artifact = json.loads(args.artifact.read_text(encoding="utf-8"))
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))
    profile = profiles[artifact["resource_profile"]]
    name = artifact["challenge_id"]
    image_ref = artifact.get("image_ref") or f'{artifact["image"]}@{artifact["digest"]}'
    health_path = artifact["health_path"]
    container_port = artifact["container_port"]

    manifest = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {name}
  namespace: challenge
  labels:
    app.kubernetes.io/name: {name}
    app.kubernetes.io/part-of: msgctf-challenges
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: {name}
  template:
    metadata:
      labels:
        app.kubernetes.io/name: {name}
    spec:
      containers:
        - name: challenge
          image: {image_ref}
          ports:
            - containerPort: {container_port}
          resources:
            requests:
              cpu: {profile["requests"]["cpu"]}
              memory: {profile["requests"]["memory"]}
            limits:
              cpu: {profile["limits"]["cpu"]}
              memory: {profile["limits"]["memory"]}
          readinessProbe:
            httpGet:
              path: {health_path}
              port: {container_port}
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: {health_path}
              port: {container_port}
            initialDelaySeconds: 15
            periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: {name}
  namespace: challenge
  labels:
    app.kubernetes.io/name: {name}
    app.kubernetes.io/part-of: msgctf-challenges
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: {name}
  ports:
    - name: http
      port: 80
      targetPort: {container_port}
"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(manifest, encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    raise SystemExit(main())
