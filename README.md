# pulse

A small uptime checker, built as an end-to-end DevOps project: a **Python** service, packaged with **Docker**, deployed on **Kubernetes**, with the cluster provisioned by **Terraform** and everything tested and shipped by a **GitHub Actions** CI/CD pipeline.

pulse checks a list of URLs on a schedule and exposes the results as JSON and as **Prometheus** metrics.

```
 git push ──► GitHub Actions
              ├─ lint (ruff) + unit tests (pytest)
              ├─ terraform fmt + validate
              ├─ docker build ─► Trivy scan (fails on HIGH/CRITICAL CVEs)
              │                └─► throwaway kind cluster ─► kubectl apply ─► smoke test
              └─ push image to ghcr.io (main branch only)

 Terraform ──► kind cluster (1 control-plane + 1 worker) + "pulse" namespace (restricted pod security)
 Kubernetes ─► ConfigMap (targets) ─► Deployment (2 replicas, probes, limits, non-root) ─► Service
```

## Endpoints

| Path | Purpose |
|---|---|
| `/healthz` | Liveness probe: the process is up |
| `/readyz` | Readiness probe: returns 503 until the first check round finishes |
| `/status` | JSON results for every target |
| `/metrics` | Prometheus metrics: `pulse_target_up`, `pulse_target_latency_seconds` |

## Run it locally

Requirements: Docker, kubectl, Terraform, kind, Python 3.12+.

```bash
# 1. Unit tests
python -m venv .venv && . .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q

# 2. Cluster + namespace
cd terraform && terraform init && terraform apply && cd ..
export KUBECONFIG=terraform/pulse-config

# 3. Build and deploy
docker build -t pulse:dev .
kind load docker-image pulse:dev --name pulse
kubectl apply -k k8s
kubectl -n pulse rollout status deploy/pulse

# 4. Try it
kubectl -n pulse port-forward svc/pulse 8080:80
curl localhost:8080/status

# Tear down
cd terraform && terraform destroy
```

Change the checked URLs in `k8s/configmap.yaml`, then `kubectl apply -k k8s` and `kubectl -n pulse rollout restart deploy/pulse`.

## Design choices

- **Config via environment variables**, injected from a ConfigMap, so the same image runs anywhere.
- **Separate liveness and readiness probes**: a pod only gets traffic once it has real data, and gets restarted if it hangs.
- **Hardened container**: multi-stage build, non-root user (uid 10001), read-only root filesystem, all Linux capabilities dropped, seccomp `RuntimeDefault`. The namespace enforces the `restricted` Pod Security Standard, so a less secure pod would be rejected.
- **Security scan in CI**: Trivy blocks the pipeline on HIGH/CRITICAL CVEs with a fix available. The first scan caught three HIGH CVEs in Starlette (pulled in by an old FastAPI pin). Upgrading the dependencies fixed them.
- **Terraform owns infrastructure, kubectl owns the app**: the cluster and namespace are long-lived infrastructure, while the app changes on every deploy. Swapping `kind_cluster` for a cloud cluster (EKS/GKE/OKE) doesn't change the app side.

## Next steps

- Provision a real cloud cluster with Terraform (free-tier VM + k3s)
- Prometheus + Grafana dashboard scraping `/metrics`
- Helm chart instead of plain manifests
