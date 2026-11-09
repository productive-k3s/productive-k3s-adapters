from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from productive_k3s_adapters.model import Service


@dataclass(frozen=True, slots=True)
class ImageMaterial:
    id: str
    repository: str
    version: str
    digest: str
    required: bool = True
    source: str | None = None


@dataclass(slots=True)
class Resolution:
    kind: str
    chart: str
    repository: str
    version: str | None
    values: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    chart_digest: str | None = None
    images: tuple[ImageMaterial, ...] = ()


class Resolver:
    def matches(self, service: Service) -> bool:
        raise NotImplementedError

    def resolve(self, service: Service) -> Resolution:
        raise NotImplementedError


def parse_image_reference(image: str) -> tuple[str, str | None, str | None]:
    reference, separator, digest = image.partition("@")
    last = reference.rsplit("/", 1)[-1]
    if ":" in last:
        repository, tag = reference.rsplit(":", 1)
    else:
        repository, tag = reference, None
    return repository, tag, digest if separator else None


def image_repository_and_tag(image: str) -> tuple[str, str | None]:
    repository, tag, digest = parse_image_reference(image)
    return repository, digest or tag
