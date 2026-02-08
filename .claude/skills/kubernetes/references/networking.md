# Kubernetes Networking Reference

Services, Ingress, and Network Policies for application exposure and security.

## Services

### ClusterIP (Internal Only)

Default service type. Accessible only within the cluster.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: default
  labels:
    app: my-app
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP
```

Access within cluster: `my-app.default.svc.cluster.local` or just `my-app`

### NodePort (Development/Testing)

Exposes service on each node's IP at a static port.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: default
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
    nodePort: 30080  # Optional: auto-assigned if omitted (30000-32767)
```

Access: `<node-ip>:30080`

### LoadBalancer (Cloud Production)

Provisions external load balancer (cloud provider required).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  namespace: default
  annotations:
    # AWS-specific annotations
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
  - name: http
    port: 80
    targetPort: 8080
  - name: https
    port: 443
    targetPort: 8443
```

### ExternalName (DNS Alias)

Maps service to external DNS name.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
  namespace: default
spec:
  type: ExternalName
  externalName: my-database.example.com
```

### Headless Service (StatefulSet)

For direct pod DNS without load balancing.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-stateful-app
spec:
  clusterIP: None  # Makes it headless
  selector:
    app: my-stateful-app
  ports:
  - port: 5432
    targetPort: 5432
```

---

## Ingress

HTTP/HTTPS routing based on host and path.

### Basic Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
```

### Multi-Service Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: multi-service-ingress
  namespace: default
spec:
  ingressClassName: nginx
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /users
        pathType: Prefix
        backend:
          service:
            name: users-service
            port:
              number: 80
      - path: /orders
        pathType: Prefix
        backend:
          service:
            name: orders-service
            port:
              number: 80
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

### Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tls-ingress
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.example.com
    secretName: myapp-tls-secret
  rules:
  - host: myapp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app
            port:
              number: 80
```

### Path Types

```yaml
# Exact: /foo matches only /foo
path: /foo
pathType: Exact

# Prefix: /foo matches /foo, /foo/, /foo/bar
path: /foo
pathType: Prefix

# ImplementationSpecific: depends on IngressClass
path: /foo
pathType: ImplementationSpecific
```

### Common Ingress Annotations

```yaml
# NGINX Ingress Controller
annotations:
  nginx.ingress.kubernetes.io/rewrite-target: /
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
  nginx.ingress.kubernetes.io/proxy-body-size: "10m"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "60"
  nginx.ingress.kubernetes.io/proxy-connect-timeout: "60"
  nginx.ingress.kubernetes.io/use-regex: "true"
  nginx.ingress.kubernetes.io/limit-rps: "100"
  nginx.ingress.kubernetes.io/enable-cors: "true"
  nginx.ingress.kubernetes.io/cors-allow-origin: "https://example.com"
```

---

## Network Policies

Control traffic flow between pods.

### Default Deny All

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: default
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
  - Ingress
  - Egress
```

### Allow Ingress from Specific Pods

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
```

### Allow Egress to Database

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-egress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Egress
  egress:
  # Allow to database
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

### Allow Ingress from Namespace

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-monitoring
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: my-app
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
```

### Allow External Traffic

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
  - Ingress
  ingress:
  - from: []  # Empty = all sources including external
    ports:
    - protocol: TCP
      port: 80
```

### Complete Application Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  # Allow from ingress controller
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8080
  # Allow from frontend in same namespace
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  # Allow to database
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  # Allow to Redis
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  # Allow DNS
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
  # Allow external HTTPS (for API calls)
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
    ports:
    - protocol: TCP
      port: 443
```

---

## Service Mesh Readiness

For Istio/Linkerd integration:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  annotations:
    # Istio sidecar injection
    sidecar.istio.io/inject: "true"
spec:
  template:
    metadata:
      labels:
        app: my-app
        version: v1
```

---

## DNS Resolution

Within the cluster:
- Same namespace: `<service-name>` → `my-app`
- Different namespace: `<service-name>.<namespace>` → `my-app.production`
- Full FQDN: `<service-name>.<namespace>.svc.cluster.local`

Pod DNS (StatefulSets):
- `<pod-name>.<service-name>.<namespace>.svc.cluster.local`
- Example: `postgres-0.postgres.default.svc.cluster.local`
