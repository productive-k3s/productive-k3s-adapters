from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Port:
    container: int
    published: int | None = None
    protocol: str = "TCP"


@dataclass(slots=True)
class Volume:
    source: str | None
    target: str
    read_only: bool = False


@dataclass(slots=True)
class Service:
    name: str
    image: str
    command: list[str] = field(default_factory=list)
    environment: dict[str, str] = field(default_factory=dict)
    ports: list[Port] = field(default_factory=list)
    volumes: list[Volume] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    replicas: int = 1
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Application:
    name: str
    services: list[Service]
    source_type: str
    source_file: str
