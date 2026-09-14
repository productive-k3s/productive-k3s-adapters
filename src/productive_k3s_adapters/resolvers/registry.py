from __future__ import annotations

from productive_k3s_adapters.model import Service
from productive_k3s_adapters.resolvers.base import Resolution
from productive_k3s_adapters.resolvers.generic import StakaterApplicationResolver
from productive_k3s_adapters.resolvers.known import MinIOResolver, PostgreSQLResolver, RedisResolver

_RESOLVERS = [PostgreSQLResolver(), RedisResolver(), MinIOResolver(), StakaterApplicationResolver()]


def resolve_service(service: Service) -> Resolution:
    for resolver in _RESOLVERS:
        if resolver.matches(service):
            return resolver.resolve(service)
    raise RuntimeError(f"No resolver found for service {service.name}")
