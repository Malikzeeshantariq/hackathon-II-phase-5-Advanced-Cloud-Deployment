# Kubernetes Troubleshooting Reference

Common issues, debugging commands, and solutions.

## Quick Diagnostic Commands

```bash
# Overview of cluster health
kubectl get nodes
kubectl get pods --all-namespaces
kubectl get events --sort-by='.lastTimestamp' -A

# Resource status
kubectl get pods,svc,deploy,hpa -n <namespace>
kubectl describe <resource> <name> -n <namespace>

# Logs
kubectl logs <pod> -n <namespace>
kubectl logs <pod> -c <container> --previous
kubectl logs -f <pod> --tail=100

# Interactive debugging
kubectl exec -it <pod> -n <namespace> -- /bin/sh
kubectl debug <pod> -it --image=busybox
```

---

## Pod Issues

### Pod Stuck in Pending

**Symptoms:** Pod remains in `Pending` state

**Check:**
```bash
kubectl describe pod <pod-name> -n <namespace>
```

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Insufficient resources | Scale cluster or reduce requests |
| Node selector mismatch | Check nodeSelector labels |
| Taints not tolerated | Add tolerations |
| PVC not bound | Check StorageClass and PV availability |
| Image pull issues | Verify imagePullSecrets |

```yaml
# Example: Add toleration for node taint
spec:
  tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "gpu"
    effect: "NoSchedule"
```

### Pod Stuck in ContainerCreating

**Check:**
```bash
kubectl describe pod <pod-name>
kubectl get events --field-selector involvedObject.name=<pod-name>
```

**Common Causes:**
- Image pull failure
- ConfigMap/Secret not found
- Volume mount failure
- Init container not completing

### Pod CrashLoopBackOff

**Symptoms:** Pod repeatedly crashes and restarts

**Debug:**
```bash
# Check logs from crashed container
kubectl logs <pod> --previous

# Check exit code
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated}'

# Check events
kubectl describe pod <pod>
```

**Common Causes:**

| Exit Code | Meaning | Solution |
|-----------|---------|----------|
| 0 | Success (but restarts) | Check if app exits unexpectedly |
| 1 | Application error | Check logs for errors |
| 137 | OOMKilled | Increase memory limit |
| 139 | Segfault | Debug application |
| 143 | SIGTERM (graceful) | Normal termination |

### Pod OOMKilled

**Symptoms:** Container killed due to memory

```bash
kubectl describe pod <pod> | grep -A5 "Last State"
```

**Solution:**
```yaml
resources:
  requests:
    memory: "512Mi"  # Increase
  limits:
    memory: "1Gi"    # Increase
```

### Pod ImagePullBackOff

**Debug:**
```bash
kubectl describe pod <pod> | grep -A5 "Events"
```

**Common Causes:**
- Wrong image name/tag
- Private registry without credentials
- Rate limiting (Docker Hub)

**Solution:**
```yaml
spec:
  imagePullSecrets:
  - name: registry-credentials
  containers:
  - name: app
    image: registry.example.com/my-app:1.0.0  # Full path
```

---

## Service Issues

### Service Not Accessible

**Debug:**
```bash
# Check service endpoints
kubectl get endpoints <service-name>

# Test from within cluster
kubectl run debug --rm -it --image=busybox -- wget -qO- <service-name>:<port>

# Check pod labels match service selector
kubectl get pods --show-labels
kubectl get svc <service-name> -o jsonpath='{.spec.selector}'
```

**Common Causes:**

| Issue | Solution |
|-------|----------|
| No endpoints | Check selector matches pod labels |
| Wrong port | Verify targetPort matches container port |
| Pod not ready | Check readiness probe |

### External Traffic Not Reaching Service

**Debug LoadBalancer:**
```bash
kubectl get svc <service-name> -o wide
kubectl describe svc <service-name>
```

**Debug Ingress:**
```bash
kubectl describe ingress <ingress-name>
kubectl get events --field-selector involvedObject.name=<ingress-name>
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

---

## Deployment Issues

### Deployment Stuck

**Check rollout status:**
```bash
kubectl rollout status deployment/<name>
kubectl describe deployment <name>
kubectl get events --field-selector involvedObject.name=<name>
```

**Common Causes:**
- New pods failing readiness probe
- Resource quota exceeded
- Image pull issues

**Rollback:**
```bash
kubectl rollout undo deployment/<name>
kubectl rollout history deployment/<name>
```

### Pods Not Receiving Traffic During Update

**Cause:** Readiness probe failing on new pods

**Solution:** Ensure readiness probe is correctly configured:
```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10  # Give app time to start
  periodSeconds: 5
  failureThreshold: 3
```

---

## Node Issues

### Node NotReady

**Debug:**
```bash
kubectl describe node <node-name>
kubectl get events --field-selector source=kubelet

# Check kubelet logs (on node)
journalctl -u kubelet -f
```

**Common Causes:**
- Disk pressure
- Memory pressure
- Network issues
- Kubelet not running

### Node Disk Pressure

**Check:**
```bash
kubectl describe node <node> | grep -A5 "Conditions"
```

**Solutions:**
- Clean up unused images: `docker system prune`
- Increase disk size
- Adjust eviction thresholds

---

## Resource Issues

### ResourceQuota Exceeded

**Check:**
```bash
kubectl describe resourcequota -n <namespace>
```

**Solution:**
- Request quota increase
- Optimize resource usage
- Clean up unused resources

### LimitRange Violations

**Check:**
```bash
kubectl describe limitrange -n <namespace>
```

---

## Networking Issues

### DNS Not Resolving

**Test DNS:**
```bash
kubectl run dnsutils --rm -it --image=tutum/dnsutils -- nslookup kubernetes.default
kubectl run dnsutils --rm -it --image=tutum/dnsutils -- nslookup <service-name>.<namespace>
```

**Check CoreDNS:**
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns
```

### Network Policy Blocking Traffic

**Debug:**
```bash
kubectl get networkpolicies -n <namespace>
kubectl describe networkpolicy <policy-name>
```

**Temporary fix (testing only):**
```bash
kubectl delete networkpolicy <policy-name> -n <namespace>
```

---

## Storage Issues

### PVC Pending

**Debug:**
```bash
kubectl describe pvc <pvc-name>
kubectl get pv
kubectl get storageclass
```

**Common Causes:**

| Issue | Solution |
|-------|----------|
| No matching PV | Create PV or use dynamic provisioning |
| StorageClass not found | Create StorageClass |
| Capacity mismatch | Request appropriate size |
| Access mode mismatch | Use supported access mode |

### Volume Mount Failed

**Check:**
```bash
kubectl describe pod <pod-name> | grep -A10 "Events"
```

---

## Debugging Containers

### Debug with Ephemeral Container

```bash
# Add debug container to running pod
kubectl debug <pod> -it --image=busybox --target=<container>

# Debug node
kubectl debug node/<node-name> -it --image=ubuntu
```

### Debug with Copy

```bash
# Create debugging copy of pod
kubectl debug <pod> -it --copy-to=debug-pod --container=debug -- /bin/sh
```

### Common Debug Images

| Image | Use Case |
|-------|----------|
| busybox | Basic utilities (wget, nslookup) |
| alpine | Lightweight Linux |
| nicolaka/netshoot | Network debugging |
| ubuntu | Full Linux environment |

---

## Useful One-Liners

```bash
# Get all pods not running
kubectl get pods -A --field-selector status.phase!=Running

# Get all failed pods
kubectl get pods -A | grep -E 'Error|CrashLoopBackOff|ImagePullBackOff'

# Get resource usage by pod
kubectl top pods --sort-by=memory -A

# Get events sorted by time
kubectl get events --sort-by='.lastTimestamp' -A

# Force delete stuck pod
kubectl delete pod <pod> --force --grace-period=0

# Get all images in use
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u

# Restart deployment
kubectl rollout restart deployment/<name>

# Get pod YAML (clean)
kubectl get pod <pod> -o yaml | kubectl neat
```

---

## Health Check Best Practices

```yaml
# Startup probe for slow-starting apps
startupProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  failureThreshold: 30  # 5 minutes to start

# Liveness probe (is app alive?)
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 0  # After startup probe
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3

# Readiness probe (can app serve traffic?)
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```
