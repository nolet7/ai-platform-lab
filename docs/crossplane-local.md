# Local Crossplane model workspace

Crossplane 2.4.1 is installed by `argocd/Application/platform-crossplane` from the pinned stable Helm chart. Its AppProject allows only the chart's required resource kinds and the resources used by this demo. Argo ignores data in Crossplane's three TLS Secrets because the chart creates them empty and Crossplane's init container populates them.

## Resource flow

`ModelWorkspace` is a namespaced Crossplane v2 composite resource (XR). The sample `ai-platform-dev/tax-classifier-demo` selects `Composition/model-workspace-local`. The composition uses `function-patch-and-transform:v0.8.2` to create, in the same namespace:

- `PersistentVolumeClaim/tax-classifier-demo-data` requesting 1 GiB on the local `standard` storage class.
- `ConfigMap/tax-classifier-demo-info` recording the model and environment.
- `Job/tax-classifier-demo-init` that mounts the PVC and writes a workspace marker. The Job also acts as the first storage consumer because `standard` uses `WaitForFirstConsumer`.

The function reports the PVC name, storage phase, and Job name in the XR status. It marks the XR Ready only after the PVC is Bound and the initialization Job has a nonempty successful completion count. This uses local KIND storage; it creates no paid cloud resources and needs no cloud credentials.

Crossplane v2 namespaced XRs replace the separate claim plus cluster-scoped XR pattern for this local design. The XR itself is the user-facing request API.

## GitOps order and ownership

| Application | Source | Owns |
|---|---|---|
| `platform-crossplane` | Crossplane stable Helm chart 2.4.1 | Core Crossplane Deployments, Services, RBAC, and TLS Secret metadata |
| `platform-crossplane-config` | `gitops/platform-infrastructure/crossplane/config` | Function, XRD, Composition, and aggregate ClusterRole |
| `platform-crossplane-demo` | `gitops/platform-infrastructure/crossplane/demo` | Sample ModelWorkspace XR |

The composed PVC, ConfigMap, and Job are owned by Crossplane through the XR. Argo manages the XR and its definitions. All three Applications disable pruning to prevent accidental deletion of local storage while the demo is evolving.

## Validation

Run from the Ubuntu repository:

```bash
kubectl get applications -n argocd | grep platform-crossplane
kubectl get functions.pkg.crossplane.io function-patch-and-transform
kubectl get xrd modelworkspaces.platform.ai
kubectl get modelworkspace tax-classifier-demo -n ai-platform-dev
kubectl get pvc tax-classifier-demo-data -n ai-platform-dev
kubectl get job tax-classifier-demo-init -n ai-platform-dev
kubectl get configmap tax-classifier-demo-info -n ai-platform-dev -o yaml
```

Live validation on 2026-09-17 showed all three Argo Applications Synced/Healthy, the Function Installed/Healthy, the XRD Established, the XR Synced/Ready, the PVC Bound at 1 GiB, and the Job Complete. Status fields were `pvcName=tax-classifier-demo-data`, `storagePhase=Bound`, and `initJobName=tax-classifier-demo-init`.

Do not delete the XR or prune its Application to reset the demo without first deciding whether the local PVC data may be discarded.