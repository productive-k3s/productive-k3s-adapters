# OpenShip hand-off example

This directory represents the boundary between OpenShip and Productive K3s Adapters.

OpenShip is expected to produce a Docker/Compose artifact. Adapters does not require OpenShip itself and does not modify it.

```text
Git repo → OpenShip → compose.yaml → pk3s-adapters convert compose → PK3S Stack
```

Run:

```bash
make convert-example
```
