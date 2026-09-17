# OpenShip whoami plus Redis adaptation

This directory represents a runnable adaptation at the boundary between OpenShip and Productive K3s Adapters.

OpenShip is expected to produce a Docker/Compose artifact. Adapters does not require OpenShip itself and does not modify it.

```text
Git repo -> OpenShip -> compose.yaml -> pk3s-adapters convert compose -> PK3S Stack
```

The Compose file models a small application that an external build tool
could emit and that can be used as a cheap smoke fixture:

- `web`: lightweight public HTTP service, resolved through the Stakater Application target.
- `cache`: Redis service, resolved through the known Redis Helm target.

The example intentionally avoids heavyweight databases, object storage, bind
mounts, and credentials. It validates the conversion path, generated Stack
shape, generic application mapping, known service mapping, and dependency
ordering without becoming expensive to run.

Run:

```bash
make smoke-adaptation
```

Or run the steps individually:

```bash
make inspect-adaptation
make adaptations-build
```

The generated candidate is written to
`.generated/adaptations/openship/whoami-redis/`. Review
`conversion-report.json`, generated Helm values, persistence, credentials, and
the `v1alpha1` Stack descriptor before publishing the result to a catalog.
