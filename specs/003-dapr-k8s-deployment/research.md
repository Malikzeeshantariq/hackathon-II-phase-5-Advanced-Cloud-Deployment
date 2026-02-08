# Research: Phase V Part B & C — Deployment

**Branch**: `003-dapr-k8s-deployment` | **Date**: 2026-02-08

## R-001: Redpanda on Minikube (Local Kafka-Compatible Broker)

**Decision**: Use official `redpanda-data/redpanda` Helm chart from `https://charts.redpanda.com/`

**Rationale**: Official chart maintained by Redpanda Data, comprehensive Kubernetes documentation, designed for Redpanda-specific optimizations. Supports minimal development mode with single-core configuration.

**Alternatives considered**:
- Bitnami Redpanda chart (less documented, not official)
- Strimzi Kafka operator (heavier resource footprint for local dev)
- Manual deployment without Helm (no state management, not reproducible)

**Key details**:
- Minimum Kubernetes version: 1.27.0
- Minimum Helm version: 3.10.0
- Development mode: `--smp=1`, `--memory=1G` for minimal resource usage
- Installation: `helm repo add redpanda https://charts.redpanda.com/`
- Pin chart version for reproducibility

---

## R-002: Oracle OKE Always Free Tier Capacity

**Decision**: Use OKE Free Tier with reduced service footprint — deploy core services only (Chat API + backend, Notification, Recurring Task). Audit service is optional and can be excluded to save resources.

**Rationale**: OKE Free Tier provides 4 ARM vCPUs (Ampere A1) + 24GB RAM total. This is insufficient for full-stack deployment with HA, but adequate for a reduced set of services with careful resource allocation. OKE control plane is free.

**Alternatives considered**:
- OKE paid tier (costs money, rejected per user preference)
- Azure AKS / Google GKE (rejected — user chose OKE free tier)
- Skip cloud deployment entirely (rejected — Part C is a deliverable)

**Key details**:
- Node shape: VM.Standard.A1.Flex (ARM only)
- Recommended: 2 nodes × 2 vCPU × 12GB RAM each
- Available storage: 100GB boot volume per node
- Architecture: ARM (aarch64) — container images MUST be built for linux/arm64
- Dapr control plane: non-HA mode (1 replica per component)
- Redpanda: excluded from cloud — use a lightweight alternative or external managed service
- Critical constraint: ARM architecture requires multi-arch Docker builds

**Resource allocation plan (OKE Free Tier)**:

| Component | vCPU | Memory | Notes |
|-----------|------|--------|-------|
| Dapr control plane (non-HA) | 0.5 | 1.5GB | placement + operator + sentry |
| Chat API + MCP | 0.3 | 512MB | Core service |
| Notification Service | 0.2 | 256MB | Lightweight consumer |
| Recurring Task Service | 0.2 | 256MB | Lightweight consumer |
| Audit Service (optional) | 0.2 | 256MB | Can be excluded |
| Dapr sidecars (×3-4) | 0.4 | 800MB | ~100-200MB each |
| Kubernetes system | 0.5 | 1GB | DNS, kube-proxy, etc. |
| **Total** | **~2.3-2.5** | **~4.5-5GB** | Within 4 vCPU / 24GB |

**Kafka alternative for OKE Free Tier**: Running Redpanda on ARM free-tier nodes is risky due to memory constraints. Options:
1. Use Redpanda Cloud free tier (external managed service)
2. Use a minimal single-node Redpanda with extreme resource limits
3. Use Dapr Pub/Sub with a PostgreSQL-backed pub/sub component (no Kafka needed)

---

## R-003: Oracle Container Registry (OCIR)

**Decision**: Use OCIR with `oracle-actions/login-ocir` GitHub Action for CI/CD authentication.

**Rationale**: Native OCI integration, free tier includes registry usage, official GitHub Action maintained by Oracle.

**Alternatives considered**:
- Docker Hub (rate limits on free tier)
- GitHub Container Registry (valid but requires separate auth for OKE)

**Key details**:
- Authentication: Auth token generated in OCI console
- Login: `docker login <region-key>.ocir.io`
- Username format: `<tenancy-namespace>/<username>`
- Image naming: `<region-key>.ocir.io/<tenancy-namespace>/<repo-name>:<tag>`
- GitHub Action: `oracle-actions/login-ocir@v1.2`
- **Critical**: Images MUST be built for `linux/arm64` for OKE free tier (ARM nodes)

---

## R-004: Dapr on Kubernetes

**Decision**: Use official `dapr/dapr` Helm chart. Non-HA mode for both local and OKE free tier. HA mode only if paid cloud tier is used.

**Rationale**: Official chart, well-documented, flexible resource configuration per component. Non-HA suitable for dev/demo environments.

**Alternatives considered**:
- Dapr CLI installation (less configurable, not declarative)
- Dapr Shared (DaemonSet mode, experimental)

**Key details**:
- Helm repository: `https://dapr.github.io/helm-charts/`
- Install: `helm repo add dapr https://dapr.github.io/helm-charts/`
- Non-HA: default (1 replica per control plane component)
- Sidecar resources: set explicitly via annotations
  - `dapr.io/sidecar-cpu-limit: "200m"`
  - `dapr.io/sidecar-memory-limit: "256Mi"`
- mTLS enabled by default
- Pin Dapr version for reproducibility

---

## R-005: GitHub Actions for OKE

**Decision**: Use `oracle-actions/configure-kubectl-oke` with OCI CLI configuration for deployment.

**Rationale**: Official Oracle GitHub Action, automated kubectl configuration, supports both OIDC and static credentials.

**Alternatives considered**:
- Manual kubeconfig management (security and maintenance burden)
- OCI DevOps service (adds complexity beyond needs)

**Key details**:
- Required GitHub secrets: OCI_AUTH_TOKEN, OKE_CLUSTER_ID, OCI_TENANCY, OCI_USER, OCI_FINGERPRINT, OCI_KEY_CONTENT, OCI_REGION
- Pipeline pattern: Build → Push to OCIR → Configure kubectl → Helm deploy
- Concurrency: Use GitHub Actions concurrency groups to prevent parallel deploys
- ARM builds: Use `docker buildx` with `--platform linux/arm64`

---

## R-006: Minikube Resource Requirements

**Decision**: Allocate 6 CPUs and 12GB RAM minimum for full local deployment.

**Rationale**: 5 services + Dapr sidecars + Dapr control plane + Redpanda + Kubernetes system requires substantial resources. 6 CPUs / 12GB is the minimum for stability.

**Key details**:
- Start command: `minikube start --cpus=6 --memory=12288 --driver=docker`
- Ideal: `--cpus=8 --memory=16384`
- Component breakdown:
  - Dapr control plane (non-HA): ~0.5 CPU, 1.5GB RAM
  - Redpanda (minimal dev): 1 CPU, 2GB RAM
  - Backend + 3 services: ~2 CPU, 4GB RAM
  - Dapr sidecars (×4): ~0.4 CPU, 800MB RAM
  - Kubernetes system: ~0.5 CPU, 1GB RAM
  - Buffer: ~1.5 CPU, 2.5GB RAM

---

## R-007: ARM Multi-Architecture Docker Builds

**Decision**: Use Docker Buildx with multi-platform builds (`linux/amd64,linux/arm64`) for all service images.

**Rationale**: OKE free tier uses ARM (Ampere A1) nodes. Local Minikube uses amd64. Images must work on both architectures.

**Key details**:
- Build command: `docker buildx build --platform linux/amd64,linux/arm64 -t <image> --push .`
- GitHub Actions: Use `docker/setup-buildx-action` and `docker/build-push-action`
- Python 3.11-slim base image supports multi-arch
- Node 20-alpine supports multi-arch
- CI/CD pipeline must build for both platforms

---

## R-008: Cloud Kafka Alternative for OKE Free Tier

**Decision**: Use Dapr Pub/Sub with PostgreSQL-backed component (`pubsub.postgresql`) for OKE free tier instead of running Redpanda/Kafka on ARM nodes.

**Rationale**: Running a full Kafka-compatible broker on OKE free tier (4 vCPUs total) would consume too many resources. Since the Neon PostgreSQL database is already external and accessible, a PostgreSQL-backed pub/sub component eliminates the need for a separate messaging cluster while still using Dapr Pub/Sub APIs (code unchanged).

**Alternatives considered**:
- Redpanda on OKE free tier (too resource-intensive for ARM nodes)
- Redpanda Cloud free tier (external service, adds dependency)
- Confluent Cloud (requires paid account for reasonable throughput)

**Key details**:
- Dapr component type: `pubsub.postgresql`
- Connection: Same Neon PostgreSQL database
- Code impact: NONE — all services use Dapr Pub/Sub API, broker is abstracted
- Local vs Cloud difference: Only the Dapr component manifest changes
  - Local: `pubsub.kafka` → Redpanda
  - Cloud (OKE free tier): `pubsub.postgresql` → Neon PostgreSQL
- Trade-off: Lower throughput than Kafka, but sufficient for demo/dev workloads
