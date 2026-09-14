from __future__ import annotations

from productive_k3s_adapters.model import Service
from productive_k3s_adapters.resolvers.base import Resolution, Resolver, image_repository_and_tag


class StakaterApplicationResolver(Resolver):
    def matches(self, service: Service) -> bool:
        return True

    def resolve(self, service: Service) -> Resolution:
        repository, tag = image_repository_and_tag(service.image)
        deployment: dict = {
            "enabled": True,
            "replicas": service.replicas,
            "image": {"repository": repository},
        }
        if tag:
            if tag.startswith("sha256:"):
                deployment["image"]["digest"] = tag
            else:
                deployment["image"]["tag"] = tag
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
            version=None,
            values=values,
            notes=notes,
        )
