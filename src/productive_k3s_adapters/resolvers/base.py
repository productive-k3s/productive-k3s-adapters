from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from productive_k3s_adapters.model import Service


@dataclass(slots=True)
class Resolution:
    kind: str
    chart: str
    repository: str
    version: str | None
    values: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


class Resolver:
    def matches(self, service: Service) -> bool:
        raise NotImplementedError

    def resolve(self, service: Service) -> Resolution:
        raise NotImplementedError


def image_repository_and_tag(image: str) -> tuple[str, str | None]:
    if "@" in image:
        repository, digest = image.split("@", 1)
        return repository, digest
    last = image.rsplit("/", 1)[-1]
    if ":" in last:
        repository, tag = image.rsplit(":", 1)
        return repository, tag
    return image, None
