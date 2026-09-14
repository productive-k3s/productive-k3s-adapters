# Productive K3s Adapters

**Productive K3s Adapters** is a build-time conversion project for turning application definitions from external ecosystems into self-contained Productive K3s artifacts.

Initial pipeline:

```text
Git repository
   ↓
OpenShip (or another producer)
   ↓
Docker Compose
   ↓
Productive K3s Adapters
   ↓
normalized application model
   ↓
resolver layer
   ├─ known services → dedicated Helm chart reference
   └─ generic services → Stakater Application values
   ↓
Productive K3s Stack artifact
   ↓
Git / catalog / Productive K3s
```

Adapters **does not deploy to Kubernetes** and is **not a runtime dependency** of Productive K3s. The generated output must remain usable after the adapter is removed.

## Status

`v0.1.0` is an initial implementation focused on Docker Compose input. It already supports:

- parsing Compose services, images, commands, environment, ports and volumes;
- normalization into an internal model;
- service recognition through pluggable resolvers;
- dedicated chart hints for PostgreSQL, Redis and MinIO;
- generic application output targeting `stakater/application`;
- generation of a self-contained Productive K3s Stack directory;
- an OpenShip-oriented example showing the expected hand-off point.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

pk3s-adapters convert compose examples/openship/compose.yaml \
  --name openship-demo \
  --output .generated/openship-demo
```

Inspect the generated artifact:

```bash
find .generated/openship-demo -maxdepth 3 -type f -print
cat .generated/openship-demo/stack.yaml
```

Run validation without generating files:

```bash
pk3s-adapters inspect compose examples/openship/compose.yaml
```

## Design rule

> A Productive K3s adapter converts external specifications into the Productive K3s standard at build time. It does not import or translate them on the fly during deployment.

See the documentation under [`docs/`](docs/README.md).
