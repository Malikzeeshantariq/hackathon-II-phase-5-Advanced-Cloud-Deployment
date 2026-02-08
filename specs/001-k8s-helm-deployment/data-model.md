# Data Model: Phase 4 Infrastructure — Kubernetes Resources

**Feature**: `001-k8s-helm-deployment`
**Date**: 2026-02-03
**Status**: Complete

---

## Overview

This document defines the Kubernetes resource model for Phase 4 deployment. All resources are managed via Helm charts.

---

## Resource Inventory

| Resource Type | Name | Namespace | Chart |
|--------------|------|-----------|-------|
| Deployment | todo-backend | default | todo-backend |
| Service | todo-backend | default | todo-backend |
| ConfigMap | todo-backend-config | default | todo-backend |
| Secret | todo-backend-secret | default | todo-backend |
| Deployment | todo-frontend | default | todo-frontend |
| Service | todo-frontend | default | todo-frontend |
| ConfigMap | todo-frontend-config | default | todo-frontend |
| Secret | todo-frontend-secret | default | todo-frontend |

---

## Backend Resources

### Deployment: todo-backend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-backend
  labels:
    app: todo-backend
    app.kubernetes.io/name: todo-backend
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: todo-backend
  template:
    metadata:
      labels:
        app: todo-backend
    spec:
      containers:
        - name: todo-backend
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 8000
              protocol: TCP
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: todo-backend-secret
                  key: database-url
            - name: BETTER_AUTH_SECRET
              valueFrom:
                secretKeyRef:
                  name: todo-backend-secret
                  key: better-auth-secret
            - name: CORS_ORIGINS
              valueFrom:
                configMapKeyRef:
                  name: todo-backend-config
                  key: cors-origins
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            limits:
              cpu: 500m
              memory: 512Mi
            requests:
              cpu: 100m
              memory: 256Mi
      securityContext:
        runAsNonRoot: true
        runAsUser: 65534
```

### Service: todo-backend

```yaml
apiVersion: v1
kind: Service
metadata:
  name: todo-backend
  labels:
    app: todo-backend
spec:
  type: ClusterIP
  ports:
    - port: 8000
      targetPort: 8000
      protocol: TCP
      name: http
  selector:
    app: todo-backend
```

### ConfigMap: todo-backend-config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: todo-backend-config
data:
  cors-origins: "http://todo-frontend:3000"
```

### Secret: todo-backend-secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: todo-backend-secret
type: Opaque
stringData:
  database-url: "{{ .Values.env.DATABASE_URL }}"
  better-auth-secret: "{{ .Values.env.BETTER_AUTH_SECRET }}"
```

---

## Frontend Resources

### Deployment: todo-frontend

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: todo-frontend
  labels:
    app: todo-frontend
    app.kubernetes.io/name: todo-frontend
    app.kubernetes.io/instance: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: todo-frontend
  template:
    metadata:
      labels:
        app: todo-frontend
    spec:
      containers:
        - name: todo-frontend
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: 3000
              protocol: TCP
          env:
            - name: BETTER_AUTH_SECRET
              valueFrom:
                secretKeyRef:
                  name: todo-frontend-secret
                  key: better-auth-secret
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: todo-frontend-secret
                  key: database-url
          livenessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 5
          resources:
            limits:
              cpu: 500m
              memory: 512Mi
            requests:
              cpu: 100m
              memory: 256Mi
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
```

### Service: todo-frontend

```yaml
apiVersion: v1
kind: Service
metadata:
  name: todo-frontend
  labels:
    app: todo-frontend
spec:
  type: NodePort
  ports:
    - port: 3000
      targetPort: 3000
      nodePort: {{ .Values.service.nodePort }}
      protocol: TCP
      name: http
  selector:
    app: todo-frontend
```

### ConfigMap: todo-frontend-config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: todo-frontend-config
data:
  # Note: NEXT_PUBLIC_* vars are build-time, so not needed at runtime
  # This configmap is for any additional runtime config
  node-env: "production"
```

### Secret: todo-frontend-secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: todo-frontend-secret
type: Opaque
stringData:
  better-auth-secret: "{{ .Values.env.BETTER_AUTH_SECRET }}"
  database-url: "{{ .Values.env.DATABASE_URL }}"
```

---

## Resource Relationships

```text
┌─────────────────────────────────────────────────────────────────────┐
│                           Kubernetes Cluster                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     todo-backend chart                       │   │
│  │                                                              │   │
│  │  ┌──────────────┐     ┌────────────────┐                    │   │
│  │  │   Secret     │────▶│   Deployment   │                    │   │
│  │  │ (credentials)│     │  (todo-backend)│                    │   │
│  │  └──────────────┘     └───────┬────────┘                    │   │
│  │                               │                              │   │
│  │  ┌──────────────┐             │                              │   │
│  │  │  ConfigMap   │─────────────┤                              │   │
│  │  │   (config)   │             │                              │   │
│  │  └──────────────┘             ▼                              │   │
│  │                         ┌──────────┐                         │   │
│  │                         │  Service │◀─────────────┐          │   │
│  │                         │(ClusterIP)│             │          │   │
│  │                         └──────────┘             │          │   │
│  └─────────────────────────────────────────────────│───────────┘   │
│                                                     │               │
│  ┌─────────────────────────────────────────────────│───────────┐   │
│  │                     todo-frontend chart          │           │   │
│  │                                                  │           │   │
│  │  ┌──────────────┐     ┌────────────────┐        │           │   │
│  │  │   Secret     │────▶│   Deployment   │────────┘           │   │
│  │  │ (credentials)│     │ (todo-frontend)│                    │   │
│  │  └──────────────┘     └───────┬────────┘                    │   │
│  │                               │                              │   │
│  │                               ▼                              │   │
│  │                         ┌──────────┐                         │   │
│  │                         │  Service │                         │   │
│  │                         │(NodePort)│◀──── Host Access        │   │
│  │                         └──────────┘                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ External Connection
                                   ▼
                          ┌──────────────────┐
                          │ Neon PostgreSQL  │
                          │   (External DB)  │
                          └──────────────────┘
```

---

## Label Standards

All resources MUST include these labels:

| Label | Value | Purpose |
|-------|-------|---------|
| `app` | `todo-backend` or `todo-frontend` | Primary selector |
| `app.kubernetes.io/name` | Chart name | Standard K8s label |
| `app.kubernetes.io/instance` | Release name | Helm instance tracking |
| `app.kubernetes.io/version` | Image tag | Version tracking |
| `app.kubernetes.io/managed-by` | `Helm` | Management tool |

---

## Resource Limits

### Backend (per pod)

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 100m | 500m |
| Memory | 256Mi | 512Mi |

### Frontend (per pod)

| Resource | Request | Limit |
|----------|---------|-------|
| CPU | 100m | 500m |
| Memory | 256Mi | 512Mi |

### Cluster Minimum Requirements

| Resource | Value |
|----------|-------|
| Minikube CPUs | 2 |
| Minikube Memory | 4GB |
| Disk | 20GB |

---

## Health Check Endpoints

### Backend

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /health` | Liveness/Readiness | HTTP 200 |

### Frontend

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `GET /` | Liveness/Readiness | HTTP 200 |

---

## Network Ports

| Service | Container Port | Service Port | External Port |
|---------|----------------|--------------|---------------|
| todo-backend | 8000 | 8000 | N/A (ClusterIP) |
| todo-frontend | 3000 | 3000 | 30000 (NodePort) |

---

## Security Configuration

### Pod Security Context

Both deployments run as non-root:

- **Backend**: `runAsUser: 65534` (nobody)
- **Frontend**: `runAsUser: 1000` (node)

### Secret Management

- Secrets are created by Helm from values
- Values MUST NOT contain actual secrets in committed files
- Use `--set` or external secret management for production
