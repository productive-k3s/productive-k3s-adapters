from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from productive_k3s_adapters.model import Application, Port, Service, Volume

_ENV_PATTERN = re.compile(r"^([^=]+)=(.*)$")


class ComposeError(ValueError):
    pass


def _environment(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return {str(k): "" if v is None else str(v) for k, v in value.items()}
    if isinstance(value, list):
        result: dict[str, str] = {}
        for item in value:
            match = _ENV_PATTERN.match(str(item))
            if match:
                result[match.group(1)] = match.group(2)
            else:
                result[str(item)] = ""
        return result
    raise ComposeError("service.environment must be a mapping or list")


def _command(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return ["/bin/sh", "-c", value]
    raise ComposeError("service.command must be a string or list")


def _ports(value: Any) -> list[Port]:
    result: list[Port] = []
    for raw in value or []:
        if isinstance(raw, int):
            result.append(Port(container=raw))
            continue
        if isinstance(raw, dict):
            target = raw.get("target")
            if target is None:
                raise ComposeError(f"port mapping missing target: {raw}")
            result.append(
                Port(
                    container=int(target),
                    published=int(raw["published"]) if raw.get("published") is not None else None,
                    protocol=str(raw.get("protocol", "tcp")).upper(),
                )
            )
            continue
        text = str(raw)
        protocol = "TCP"
        if "/" in text:
            text, proto = text.rsplit("/", 1)
            protocol = proto.upper()
        parts = text.split(":")
        if len(parts) == 1:
            result.append(Port(container=int(parts[0]), protocol=protocol))
        elif len(parts) >= 2:
            result.append(Port(container=int(parts[-1]), published=int(parts[-2]), protocol=protocol))
    return result


def _volumes(value: Any) -> list[Volume]:
    result: list[Volume] = []
    for raw in value or []:
        if isinstance(raw, dict):
            target = raw.get("target")
            if not target:
                raise ComposeError(f"volume mapping missing target: {raw}")
            result.append(Volume(source=raw.get("source"), target=str(target), read_only=bool(raw.get("read_only", False))))
            continue
        parts = str(raw).split(":")
        if len(parts) == 1:
            result.append(Volume(source=None, target=parts[0]))
        else:
            result.append(Volume(source=parts[0], target=parts[1], read_only=(len(parts) > 2 and parts[2] == "ro")))
    return result


def parse_compose(path: str | Path, name: str | None = None) -> Application:
    source = Path(path)
    if not source.exists():
        raise ComposeError(f"Compose file does not exist: {source}")

    data = yaml.safe_load(source.read_text()) or {}
    services_data = data.get("services")
    if not isinstance(services_data, dict) or not services_data:
        raise ComposeError("Compose file must define at least one service")

    services: list[Service] = []
    for service_name, raw in services_data.items():
        raw = raw or {}
        image = raw.get("image")
        if not image:
            build = raw.get("build")
            if build:
                raise ComposeError(
                    f"service '{service_name}' uses build without image; Adapters requires a built image reference"
                )
            raise ComposeError(f"service '{service_name}' does not define image")

        depends = raw.get("depends_on", [])
        if isinstance(depends, dict):
            depends = list(depends.keys())

        replicas = 1
        deploy = raw.get("deploy") or {}
        if deploy.get("replicas") is not None:
            replicas = int(deploy["replicas"])

        services.append(
            Service(
                name=str(service_name),
                image=str(image),
                command=_command(raw.get("command")),
                environment=_environment(raw.get("environment")),
                ports=_ports(raw.get("ports")),
                volumes=_volumes(raw.get("volumes")),
                depends_on=[str(v) for v in depends],
                replicas=replicas,
                raw=raw,
            )
        )

    return Application(
        name=name or source.parent.name or "application",
        services=services,
        source_type="docker-compose",
        source_file=str(source),
    )
