# OpenShip control-plane adaptation

This adaptation is derived from the OpenShip self-hosted Docker Compose shape,
but is intentionally adjusted for a first Kubernetes-safe Productive K3S
conversion.

Included:

- Postgres
- Redis
- OpenShip API
- OpenShip dashboard

Intentionally excluded in this first pass:

- OpenResty `edge` container with host networking
- host Docker socket mounting
- container-to-host SSH control channel
- host bind mounts for certificates, ACME, static assets, and OpenResty config

Those Docker-specific capabilities need explicit Productive K3S design before
they can be considered production-safe. This adaptation validates that the
OpenShip control plane can be generated, installed, and reached on k3s through
the adapter artifact path.

The API is configured with `OPENSHIP_AUTH_MODE=local` so the dashboard can be
used from a browser outside the VM once it is exposed through NodePort or
Ingress. When exposing the dashboard, set `OPENSHIP_PUBLIC_URL` to the external
URL used by the browser.

The secrets in `compose.yaml` are disposable verification defaults. Replace
them before using this as anything other than a local validation artifact.
