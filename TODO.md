# Backlog

## Near term
- Confirm the canonical Productive K3s Stack schema and align `stack.yaml` exactly with it.
- Add a resolver registry loaded from declarative YAML metadata.
- Add chart-version discovery/pinning policy.
- Expand Compose support: healthcheck, configs, secrets, networks, depends_on conditions.
- Add conversion diagnostics with source line information.
- Add `--strict` mode that fails on unsupported Compose fields.
- Add optional Helm template validation when Helm is available.

## Later
- Kubernetes manifest adapter.
- Kustomize adapter.
- Nomad adapter.
- OpenShift manifest adapter if needed.
- Catalog publication helper that creates a candidate catalog entry but never publishes automatically.
