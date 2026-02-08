---
name: kubernetes
description: |
  Deploy and scale containerized applications on Kubernetes from hello world to production.
  This skill should be used when users need to create Kubernetes manifests, deploy applications,
  configure services, set up scaling, manage configurations, or troubleshoot K8s workloads.
  Covers pods, deployments, services, ingress, storage, security, and production patterns.
---

# Kubernetes Deployment Skill

Build and deploy containerized applications on Kubernetes - from simple hello world deployments to production-grade systems with autoscaling, security, and high availability.

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing Dockerfiles, K8s manifests, Helm charts, CI/CD configs |
| **Conversation** | Application type, replicas, resource needs, environment |
| **Skill References** | Patterns from `references/` (workloads, networking, security) |
| **User Guidelines** | Team conventions, naming standards, environment constraints |

Only ask user for THEIR specific requirements (domain expertise is in this skill).

## What This Skill Does

- Creates Kubernetes manifests (Deployments, Services, Ingress, ConfigMaps, etc.)
- Configures horizontal pod autoscaling (HPA)
- Sets up persistent storage (PVC/PV)
- Implements security (RBAC, NetworkPolicies, Pod Security)
- Generates production-ready configurations with health checks and resource limits
- Provides kubectl commands for deployment and debugging

## What This Skill Does NOT Do

- Provision Kubernetes clusters (use cloud provider or kubeadm)
- Build Docker images (use docker-fastapi skill or Dockerfile skill)
- Manage CI/CD pipelines (GitOps tools like ArgoCD)
- Configure service meshes (Istio, Linkerd)

---

## Required Clarifications

Before generating manifests, gather:

| Clarification | Options | Default |
|---------------|---------|---------|
| **Application Type** | Web app, API, Worker, CronJob, StatefulDB | Web app |
| **Replicas** | Number of pod replicas | 2 |
| **Port** | Container port to expose | 8080 |
| **Resources** | CPU/Memory requests and limits | See defaults |
| **Exposure** | ClusterIP, NodePort, LoadBalancer, Ingress | ClusterIP |
| **Environment** | dev, staging, production | dev |

### Resource Defaults by Environment

```
dev:     cpu: 100m/500m,  memory: 128Mi/512Mi
staging: cpu: 250m/1000m, memory: 256Mi/1Gi
prod:    cpu: 500m/2000m, memory: 512Mi/2Gi
```

---

## Workflow

```
1. Gather Requirements
   └─ App type, image, port, replicas, environment

2. Select Workload Type
   ├─ Stateless web/API → Deployment
   ├─ Database/stateful → StatefulSet
   ├─ Node-level service → DaemonSet
   ├─ One-time task → Job
   └─ Scheduled task → CronJob

3. Generate Manifests
   ├─ Workload (Deployment/StatefulSet/etc.)
   ├─ Service (exposure type)
   ├─ ConfigMap/Secret (if config needed)
   ├─ Ingress (if external access)
   ├─ HPA (if autoscaling)
   ├─ PVC (if storage needed)
   └─ NetworkPolicy (if security required)

4. Apply & Verify
   └─ kubectl commands with verification steps
```

---

## Manifest Generation Standards

### Metadata Requirements

Every manifest MUST include:

```yaml
apiVersion: <api-version>
kind: <resource-kind>
metadata:
  name: <app-name>
  namespace: <namespace>  # Always explicit
  labels:
    app.kubernetes.io/name: <app-name>
    app.kubernetes.io/version: "<version>"
    app.kubernetes.io/component: <component>
    app.kubernetes.io/managed-by: kubectl
```

### Container Requirements

Every container MUST have:

```yaml
containers:
- name: <container-name>
  image: <image>:<tag>  # NEVER use :latest
  imagePullPolicy: IfNotPresent
  ports:
  - containerPort: <port>
    name: http
  resources:
    requests:
      cpu: "<cpu-request>"
      memory: "<memory-request>"
    limits:
      cpu: "<cpu-limit>"
      memory: "<memory-limit>"
  livenessProbe:
    httpGet:
      path: /health
      port: http
    initialDelaySeconds: 15
    periodSeconds: 20
  readinessProbe:
    httpGet:
      path: /ready
      port: http
    initialDelaySeconds: 5
    periodSeconds: 10
```

### Security Context (Production)

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

---

## Quick Reference: Workload Selection

| Use Case | Resource | Key Config |
|----------|----------|------------|
| Web apps, APIs, microservices | Deployment | replicas, strategy |
| Databases, queues, stateful apps | StatefulSet | serviceName, volumeClaimTemplates |
| Log collectors, monitoring agents | DaemonSet | nodeSelector (optional) |
| Batch processing, migrations | Job | completions, parallelism |
| Scheduled tasks, backups | CronJob | schedule (cron format) |

## Quick Reference: Service Types

| Type | Use Case | Access |
|------|----------|--------|
| ClusterIP | Internal services | Within cluster only |
| NodePort | Development/testing | node-ip:30000-32767 |
| LoadBalancer | Production external | Cloud LB IP |
| ExternalName | External services | DNS alias |

## Quick Reference: kubectl Commands

```bash
# Apply manifests
kubectl apply -f <manifest.yaml>
kubectl apply -f <directory>/

# View resources
kubectl get pods,svc,deploy -n <namespace>
kubectl describe pod <pod-name> -n <namespace>

# Debug
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -c <container> --previous
kubectl exec -it <pod-name> -n <namespace> -- /bin/sh

# Scale
kubectl scale deployment <name> --replicas=<n>

# Rollout
kubectl rollout status deployment/<name>
kubectl rollout history deployment/<name>
kubectl rollout undo deployment/<name>

# Context
kubectl config use-context <context>
kubectl config set-context --current --namespace=<ns>
```

---

## Production Checklist

Before deploying to production, verify:

### Resources & Scaling
- [ ] Resource requests AND limits set for all containers
- [ ] HPA configured with appropriate min/max replicas
- [ ] Pod Disruption Budget (PDB) defined

### Health & Reliability
- [ ] Liveness probe configured (restarts unhealthy pods)
- [ ] Readiness probe configured (controls traffic routing)
- [ ] Startup probe for slow-starting apps (optional)

### Security
- [ ] No `:latest` image tags - use specific versions
- [ ] SecurityContext with non-root user
- [ ] Secrets used for sensitive data (not ConfigMaps)
- [ ] NetworkPolicies restrict pod communication
- [ ] RBAC least-privilege access

### Configuration
- [ ] ConfigMaps for non-sensitive config
- [ ] Environment-specific values externalized
- [ ] No hardcoded URLs or credentials

### Storage (if needed)
- [ ] PVC with appropriate StorageClass
- [ ] Backup strategy for persistent data

### Observability
- [ ] Labels for filtering and selection
- [ ] Annotations for tooling integration
- [ ] Logging to stdout/stderr

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Bad | Do This Instead |
|--------------|--------------|-----------------|
| `:latest` image tag | Unpredictable deployments | Use semantic versioning |
| No resource limits | Resource contention | Set requests AND limits |
| Root containers | Security vulnerability | runAsNonRoot: true |
| Secrets in ConfigMaps | Exposed credentials | Use Secret resources |
| No health probes | Stale pods serve traffic | Configure liveness/readiness |
| hostPath volumes | Node-specific data | Use PVC with StorageClass |
| Single replica in prod | No high availability | Minimum 2 replicas + PDB |
| Hardcoded config | Environment coupling | Use ConfigMaps/env vars |

---

## Reference Files

For detailed patterns and examples, see:

| File | Content |
|------|---------|
| `references/workloads.md` | Deployment, StatefulSet, DaemonSet, Job, CronJob patterns |
| `references/networking.md` | Service, Ingress, NetworkPolicy configurations |
| `references/storage.md` | PV, PVC, StorageClass patterns |
| `references/security.md` | RBAC, Pod Security, Secrets management |
| `references/scaling.md` | HPA, VPA, cluster autoscaling |
| `references/troubleshooting.md` | Common issues and debugging commands |
| `assets/deployment-template.yaml` | Base deployment template |
| `assets/service-template.yaml` | Base service template |
