# Kubernetes Scaling Reference

Horizontal Pod Autoscaler, manual scaling, and resource management.

## Manual Scaling

### Scale Deployment

```bash
# Scale to specific replica count
kubectl scale deployment my-app --replicas=5

# Scale multiple deployments
kubectl scale deployment app1 app2 --replicas=3

# Scale StatefulSet
kubectl scale statefulset postgres --replicas=3
```

### Scale via Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5  # Directly set replica count
```

---

## Horizontal Pod Autoscaler (HPA)

### Basic CPU-Based HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
  namespace: default
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### CPU and Memory HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### HPA with Scaling Behavior

Control scale up/down speed.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0  # Scale up immediately
      policies:
      - type: Percent
        value: 100  # Double pods
        periodSeconds: 15
      - type: Pods
        value: 4  # Or add 4 pods
        periodSeconds: 15
      selectPolicy: Max  # Use whichever adds more pods
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scale down
      policies:
      - type: Percent
        value: 10  # Remove 10% of pods
        periodSeconds: 60
      selectPolicy: Min  # Use whichever removes fewer pods
```

### Custom Metrics HPA

Requires metrics adapter (Prometheus Adapter, KEDA, etc.)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: queue-consumer-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: queue-consumer
  minReplicas: 1
  maxReplicas: 100
  metrics:
  # Custom metric: messages in queue
  - type: External
    external:
      metric:
        name: rabbitmq_queue_messages
        selector:
          matchLabels:
            queue: my-queue
      target:
        type: Value
        value: "100"  # Scale when queue > 100 messages
  # Per-pod custom metric
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### HPA Requirements

1. **Metrics Server** must be deployed
2. **Resource requests** must be defined on containers
3. Target resource must support scaling (Deployment, StatefulSet, ReplicaSet)

Install Metrics Server:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

---

## Resource Management

### Resource Requests and Limits

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    image: my-app:1.0.0
    resources:
      requests:
        cpu: "100m"      # 0.1 CPU core (guaranteed)
        memory: "128Mi"  # 128 MiB (guaranteed)
      limits:
        cpu: "500m"      # 0.5 CPU core (max)
        memory: "512Mi"  # 512 MiB (max, OOMKilled if exceeded)
```

### Resource Units

**CPU:**
- `1` = 1 CPU core
- `1000m` = 1 CPU core
- `100m` = 0.1 CPU core (100 millicores)

**Memory:**
- `128Mi` = 128 mebibytes
- `1Gi` = 1 gibibyte
- `128M` = 128 megabytes (decimal)

### Recommended Resource Guidelines

| Environment | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------------|-------------|-----------|----------------|--------------|
| Development | 50m | 200m | 64Mi | 256Mi |
| Staging | 100m | 500m | 128Mi | 512Mi |
| Production | 250m-500m | 1000m-2000m | 256Mi-512Mi | 1Gi-2Gi |

---

## LimitRange

Set default and max resources per namespace.

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: default
spec:
  limits:
  - type: Container
    default:
      cpu: "200m"
      memory: "256Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "4Gi"
    min:
      cpu: "50m"
      memory: "64Mi"
  - type: Pod
    max:
      cpu: "4"
      memory: "8Gi"
```

---

## ResourceQuota

Limit total resources per namespace.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: development
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
    persistentvolumeclaims: "10"
    services.loadbalancers: "2"
```

---

## Pod Disruption Budget (PDB)

Ensure availability during voluntary disruptions.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
  namespace: default
spec:
  minAvailable: 2  # Always keep at least 2 pods
  selector:
    matchLabels:
      app: my-app
```

Or use maxUnavailable:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-app-pdb
spec:
  maxUnavailable: 1  # At most 1 pod unavailable
  selector:
    matchLabels:
      app: my-app
```

### PDB Best Practices

| Scenario | Configuration |
|----------|---------------|
| Critical service (3 replicas) | minAvailable: 2 |
| High availability (5+ replicas) | maxUnavailable: 1 |
| Rolling updates | maxUnavailable: 25% |

---

## Vertical Pod Autoscaler (VPA)

Automatically adjust resource requests/limits.

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updatePolicy:
    updateMode: "Auto"  # Off, Initial, Recreate, Auto
  resourcePolicy:
    containerPolicies:
    - containerName: app
      minAllowed:
        cpu: "100m"
        memory: "128Mi"
      maxAllowed:
        cpu: "2"
        memory: "4Gi"
      controlledResources: ["cpu", "memory"]
```

**VPA Modes:**
- `Off`: Only recommendations (no changes)
- `Initial`: Set requests at pod creation
- `Recreate`: Recreate pods to apply changes
- `Auto`: Recreate or in-place update

---

## Monitoring Scaling

```bash
# Check HPA status
kubectl get hpa

# Detailed HPA info
kubectl describe hpa my-app-hpa

# Current resource usage
kubectl top pods
kubectl top nodes

# Watch scaling events
kubectl get events --field-selector reason=SuccessfulRescale

# Check metrics
kubectl get --raw /apis/metrics.k8s.io/v1beta1/pods
```

---

## Scaling Decision Tree

```
Is load variable?
├─ Yes → HPA
│   ├─ CPU/Memory based → Resource metrics
│   └─ Custom metric → External metrics + adapter
└─ No → Static replicas

Is resource usage unpredictable?
├─ Yes → VPA (recommendation mode first)
└─ No → Static resource requests

Need guaranteed availability during disruptions?
├─ Yes → PDB required
└─ No → Optional but recommended

Multiple metric types needed?
├─ Yes → Use multiple HPA metrics (highest wins)
└─ No → Single metric sufficient
```
