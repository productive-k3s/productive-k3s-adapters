from __future__ import annotations

from productive_k3s_adapters.model import Service
from productive_k3s_adapters.resolvers.base import (
    ImageMaterial,
    Resolution,
    Resolver,
    parse_image_reference,
)


class StakaterApplicationResolver(Resolver):
    chart_version = "9.3.2"
    chart_digest = "sha256:1c17fecf71c676868282a74462d82c7b252b244f2a2a3cf8f56b2825298f59c0"

    def matches(self, service: Service) -> bool:
        return True

    def resolve(self, service: Service) -> Resolution:
        repository, tag, digest = parse_image_reference(service.image)
        deployment: dict = {
            "enabled": True,
            "replicas": service.replicas,
            "image": {"repository": repository},
            "containerSecurityContext": {
                "readOnlyRootFilesystem": False,
                "runAsNonRoot": False,
            },
        }
        if tag:
            deployment["image"]["tag"] = tag
        if digest:
            deployment["image"]["digest"] = digest
        if service.command:
            deployment["command"] = service.command
        if service.environment:
            deployment["env"] = {
                key: {"value": value} for key, value in sorted(service.environment.items())
            }
        if service.ports:
            deployment["ports"] = [
                {"name": f"port-{p.container}", "containerPort": p.container, "protocol": p.protocol}
                for p in service.ports
            ]

        values: dict = {"applicationName": service.name, "deployment": deployment}
        if service.ports:
            values["service"] = {
                "enabled": True,
                "ports": [
                    {
                        "name": f"port-{p.container}",
                        "port": p.published or p.container,
                        "targetPort": p.container,
                        "protocol": p.protocol,
                    }
                    for p in service.ports
                ],
            }

        notes = []
        if service.volumes:
            notes.append("Compose volumes were detected; review generated TODOs for persistence mapping.")
        return Resolution(
            kind="generic-application",
            chart="stakater/application",
            repository="https://stakater.github.io/stakater-charts",
            version=self.chart_version,
            values=values,
            notes=notes,
            chart_digest=self.chart_digest,
            images=(
                ImageMaterial(
                    id="container-image",
                    repository=repository,
                    version=tag or digest or "unversioned",
                    digest=digest or "",
                    source=repository,
                ),
            ),
        )
