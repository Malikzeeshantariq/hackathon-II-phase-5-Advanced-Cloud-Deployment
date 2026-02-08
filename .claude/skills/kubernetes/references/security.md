# Kubernetes Security Reference

RBAC, Pod Security, Secrets, and security best practices.

## RBAC (Role-Based Access Control)

### ServiceAccount

Identity for pods and processes.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: default
automountServiceAccountToken: false  # Explicit control
```

### Role (Namespace-scoped)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "watch", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]
```

### RoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### ClusterRole (Cluster-scoped)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: namespace-reader
rules:
- apiGroups: [""]
  resources: ["namespaces"]
  verbs: ["get", "watch", "list"]
- apiGroups: [""]
  resources: ["nodes"]
  verbs: ["get", "list"]
```

### ClusterRoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-namespaces
subjects:
- kind: ServiceAccount
  name: monitoring-sa
  namespace: monitoring
roleRef:
  kind: ClusterRole
  name: namespace-reader
  apiGroup: rbac.authorization.k8s.io
```

### Common RBAC Verbs

| Verb | Description |
|------|-------------|
| get | Read single resource |
| list | List resources |
| watch | Watch for changes |
| create | Create resources |
| update | Update resources |
| patch | Partially update resources |
| delete | Delete resources |
| deletecollection | Delete multiple resources |

### Application ServiceAccount with Minimal Permissions

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app-sa
  namespace: production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: my-app-role
  namespace: production
rules:
# Read ConfigMaps
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["my-app-config"]
  verbs: ["get"]
# Read Secrets
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["my-app-secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: my-app-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: my-app-sa
  namespace: production
roleRef:
  kind: Role
  name: my-app-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Pod Security Standards

### Enforce via Namespace Labels

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### Security Levels

| Level | Description |
|-------|-------------|
| privileged | No restrictions (use for system workloads) |
| baseline | Minimal restrictions, prevents known vulnerabilities |
| restricted | Heavily restricted, current best practices |

### Restricted Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: my-app:1.0.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
          - ALL
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Secrets Management

### Create Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: default
type: Opaque
data:
  # Base64 encoded values
  db-password: cGFzc3dvcmQxMjM=
  api-key: YWJjMTIzZGVm
```

Or with stringData (auto-encoded):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  db-password: password123
  api-key: abc123def
```

### Secret Types

| Type | Use Case |
|------|----------|
| Opaque | Arbitrary user-defined data |
| kubernetes.io/tls | TLS certificate and key |
| kubernetes.io/dockerconfigjson | Docker registry credentials |
| kubernetes.io/basic-auth | Basic authentication |
| kubernetes.io/ssh-auth | SSH private key |
| kubernetes.io/service-account-token | ServiceAccount token |

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

Or create with kubectl:
```bash
kubectl create secret tls tls-secret \
  --cert=path/to/cert.pem \
  --key=path/to/key.pem
```

### Docker Registry Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>
```

Or create with kubectl:
```bash
kubectl create secret docker-registry registry-credentials \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass
```

### Using Secrets in Pods

```yaml
apiVersion: v1
kind: Pod
spec:
  imagePullSecrets:
  - name: registry-credentials
  containers:
  - name: app
    image: registry.example.com/my-app:1.0.0
    env:
    # Single value from secret
    - name: DB_PASSWORD
      valueFrom:
        secretKeyRef:
          name: app-secrets
          key: db-password
    # All values as env vars
    envFrom:
    - secretRef:
        name: app-secrets
        optional: false
    # Mount as files
    volumeMounts:
    - name: secrets
      mountPath: /etc/secrets
      readOnly: true
  volumes:
  - name: secrets
    secret:
      secretName: app-secrets
      defaultMode: 0400
```

---

## Network Security

### Default Deny All

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Allow Only Required Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  - to:  # Allow DNS
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

---

## Security Best Practices Checklist

### Container Security
- [ ] Non-root user (`runAsNonRoot: true`)
- [ ] Read-only filesystem (`readOnlyRootFilesystem: true`)
- [ ] No privilege escalation (`allowPrivilegeEscalation: false`)
- [ ] Drop all capabilities (`capabilities.drop: ["ALL"]`)
- [ ] Specific image versions (no `:latest`)
- [ ] Image from trusted registry
- [ ] Seccomp profile enabled

### Pod Security
- [ ] ServiceAccount with minimal permissions
- [ ] automountServiceAccountToken: false (when not needed)
- [ ] Pod Security Standard enforced (restricted)
- [ ] Resource limits set

### Network Security
- [ ] NetworkPolicies in place
- [ ] Default deny all traffic
- [ ] Egress restricted to required destinations

### Secrets Management
- [ ] Secrets stored in Kubernetes Secrets (not ConfigMaps)
- [ ] Secrets mounted as files (not env vars when possible)
- [ ] Encryption at rest enabled
- [ ] External secrets manager for production (Vault, AWS Secrets Manager)

### RBAC
- [ ] Least privilege principle
- [ ] No cluster-admin for applications
- [ ] Namespace-scoped roles when possible
- [ ] Regular audit of permissions

---

## Security Scanning

### Pod Security Admission Check

```bash
# Dry-run to check if pod meets restricted standard
kubectl label --dry-run=server --overwrite ns default \
  pod-security.kubernetes.io/enforce=restricted
```

### Audit Commands

```bash
# List all cluster roles
kubectl get clusterroles

# Check role permissions
kubectl describe role <role-name> -n <namespace>

# List all role bindings
kubectl get rolebindings,clusterrolebindings --all-namespaces

# Check who can perform action
kubectl auth can-i create pods --as=system:serviceaccount:default:my-app-sa
```
