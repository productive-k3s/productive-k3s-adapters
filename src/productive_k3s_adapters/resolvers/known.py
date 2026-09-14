from __future__ import annotations

from productive_k3s_adapters.model import Service
from productive_k3s_adapters.resolvers.base import Resolution, Resolver


class _ImagePrefixResolver(Resolver):
    image_names: tuple[str, ...] = ()
    chart: str = ""
    repository: str = ""

    def matches(self, service: Service) -> bool:
        image = service.image.lower().split("@", 1)[0]
        base = image.rsplit("/", 1)[-1].split(":", 1)[0]
        return base in self.image_names


class PostgreSQLResolver(_ImagePrefixResolver):
    image_names = ("postgres", "postgresql")
    chart = "bitnami/postgresql"
    repository = "https://charts.bitnami.com/bitnami"

    def resolve(self, service: Service) -> Resolution:
        values = {}
        if service.environment.get("POSTGRES_DB"):
            values.setdefault("auth", {})["database"] = service.environment["POSTGRES_DB"]
        if service.environment.get("POSTGRES_USER"):
            values.setdefault("auth", {})["username"] = service.environment["POSTGRES_USER"]
        if service.environment.get("POSTGRES_PASSWORD"):
            values.setdefault("auth", {})["password"] = service.environment["POSTGRES_PASSWORD"]
        return Resolution("known-service", self.chart, self.repository, None, values, ["Review persistence and credentials before production use."])


class RedisResolver(_ImagePrefixResolver):
    image_names = ("redis",)
    chart = "bitnami/redis"
    repository = "https://charts.bitnami.com/bitnami"

    def resolve(self, service: Service) -> Resolution:
        return Resolution("known-service", self.chart, self.repository, None, {"architecture": "standalone"}, ["Review authentication and persistence before production use."])


class MinIOResolver(_ImagePrefixResolver):
    image_names = ("minio",)
    chart = "minio/minio"
    repository = "https://charts.min.io/"

    def resolve(self, service: Service) -> Resolution:
        values = {}
        if service.environment.get("MINIO_ROOT_USER"):
            values["rootUser"] = service.environment["MINIO_ROOT_USER"]
        if service.environment.get("MINIO_ROOT_PASSWORD"):
            values["rootPassword"] = service.environment["MINIO_ROOT_PASSWORD"]
        return Resolution("known-service", self.chart, self.repository, None, values, ["Review chart compatibility/version before production use."])
