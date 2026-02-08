# Kubernetes Storage Reference

Persistent storage patterns for stateful applications.

## Storage Overview

| Resource | Purpose | Scope |
|----------|---------|-------|
| Volume | Temporary storage tied to Pod | Pod |
| PersistentVolume (PV) | Cluster storage resource | Cluster |
| PersistentVolumeClaim (PVC) | Request for storage | Namespace |
| StorageClass | Dynamic provisioning template | Cluster |

---

## Ephemeral Volumes

### emptyDir (Scratch Space)

Temporary storage, deleted when Pod terminates.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    image: my-app:1.0.0
    volumeMounts:
    - name: scratch
      mountPath: /tmp
    - name: cache
      mountPath: /cache
  volumes:
  - name: scratch
    emptyDir: {}
  - name: cache
    emptyDir:
      medium: Memory  # Use RAM
      sizeLimit: 256Mi
```

### ConfigMap Volume

Mount configuration files.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  config.yaml: |
    server:
      port: 8080
    database:
      host: postgres
---
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    volumeMounts:
    - name: config
      mountPath: /etc/config
      readOnly: true
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: config.yaml
        path: config.yaml
        mode: 0644
```

### Secret Volume

Mount sensitive data.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  db-password: cGFzc3dvcmQxMjM=  # base64 encoded
---
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
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

### Projected Volume (Multiple Sources)

Combine multiple volume sources.

```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    volumeMounts:
    - name: all-in-one
      mountPath: /projected
      readOnly: true
  volumes:
  - name: all-in-one
    projected:
      sources:
      - configMap:
          name: app-config
      - secret:
          name: app-secrets
      - downwardAPI:
          items:
          - path: labels
            fieldRef:
              fieldPath: metadata.labels
```

---

## Persistent Storage

### PersistentVolumeClaim (PVC)

Request storage from a StorageClass.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: default
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

### Using PVC in Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 1  # Single replica with RWO storage
  template:
    spec:
      containers:
      - name: app
        image: my-app:1.0.0
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: data-pvc
```

### StatefulSet with volumeClaimTemplates

Automatic PVC creation per replica.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

Creates: `data-postgres-0`, `data-postgres-1`, `data-postgres-2`

---

## Access Modes

| Mode | Abbreviation | Description |
|------|--------------|-------------|
| ReadWriteOnce | RWO | Single node read-write |
| ReadOnlyMany | ROX | Many nodes read-only |
| ReadWriteMany | RWX | Many nodes read-write |
| ReadWriteOncePod | RWOP | Single pod read-write |

---

## StorageClass

### Dynamic Provisioning Template

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iopsPerGB: "10"
  fsType: ext4
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### Cloud Provider StorageClasses

```yaml
# AWS EBS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: aws-ebs-gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iopsPerGB: "10"
  throughput: "125"
volumeBindingMode: WaitForFirstConsumer
---
# GCP Persistent Disk
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gcp-pd-ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
volumeBindingMode: WaitForFirstConsumer
---
# Azure Disk
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-disk-premium
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
volumeBindingMode: WaitForFirstConsumer
```

### Local Development (minikube/kind)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

---

## Reclaim Policies

| Policy | Behavior |
|--------|----------|
| Retain | Keep PV after PVC deletion (manual cleanup) |
| Delete | Delete PV and underlying storage |
| Recycle | (Deprecated) Basic scrub and reuse |

---

## Volume Binding Modes

| Mode | Behavior |
|------|----------|
| Immediate | Bind PVC to PV immediately |
| WaitForFirstConsumer | Wait until Pod using PVC is scheduled |

Use `WaitForFirstConsumer` for topology-aware provisioning.

---

## PersistentVolume (Manual Provisioning)

For pre-provisioned storage or on-premises.

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs-pv
spec:
  capacity:
    storage: 100Gi
  accessModes:
  - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  nfs:
    server: nfs-server.example.com
    path: /exports/data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: nfs-pvc
spec:
  accessModes:
  - ReadWriteMany
  storageClassName: nfs
  resources:
    requests:
      storage: 50Gi
```

---

## Volume Snapshots

### Create Snapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: data-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: data-pvc
```

### Restore from Snapshot

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-restored
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
  dataSource:
    name: data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

---

## Best Practices

1. **Always use StorageClasses** for dynamic provisioning
2. **Use WaitForFirstConsumer** for multi-zone clusters
3. **Set appropriate reclaim policy** (Delete for dev, Retain for prod)
4. **Enable volume expansion** for growing storage needs
5. **Use RWO unless RWX is required** (RWX has performance overhead)
6. **Implement backup strategy** with snapshots or external tools
7. **Monitor storage usage** to prevent capacity issues
