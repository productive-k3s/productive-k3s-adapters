from __future__ import annotations

from productive_k3s_adapters.model import Service
from productive_k3s_adapters.resolvers.base import ImageMaterial, Resolution, Resolver


def _image_values(repository: str, tag: str, digest: str) -> dict[str, str]:
    registry, image_repository = repository.split("/", 1)
    return {
        "registry": registry,
        "repository": image_repository,
        "tag": tag,
        "digest": digest,
    }


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
    chart_version = "18.12.4"
    chart_digest = "sha256:cdea1be659dd2c9b573adaee286b426911bcc4ddd4d7e0111df65309e38669fb"
    postgres = ImageMaterial(
        "postgresql-image",
        "docker.io/bitnamilegacy/postgresql",
        "17.6.0-debian-12-r4",
        "sha256:926356130b77d5742d8ce605b258d35db9b62f2f8fd1601f9dbaef0c8a710a8d",
    )
    exporter = ImageMaterial(
        "postgres-exporter-image",
        "docker.io/bitnamilegacy/postgres-exporter",
        "0.17.1-debian-12-r16",
        "sha256:6499edcf396cb75dd73d17f89e4c8c7ba9cab7a6e7abeb289009f9210e6762b0",
        required=False,
    )
    os_shell = ImageMaterial(
        "os-shell-image",
        "docker.io/bitnamilegacy/os-shell",
        "12-debian-12-r51",
        "sha256:77e65e9d633ec1463f8bea185763aa7ef91e5ddbe0b60beb1b0b5d4da58882b6",
        required=False,
    )

    def resolve(self, service: Service) -> Resolution:
        values = {
            "global": {"security": {"allowInsecureImages": True}},
            "fullnameOverride": service.name,
            "image": _image_values(self.postgres.repository, self.postgres.version, self.postgres.digest),
            "primary": {
                "persistence": {
                    "enabled": False,
                },
            },
            "metrics": {
                "image": _image_values(self.exporter.repository, self.exporter.version, self.exporter.digest),
            },
            "volumePermissions": {
                "image": _image_values(self.os_shell.repository, self.os_shell.version, self.os_shell.digest),
            },
        }
        if service.environment.get("POSTGRES_DB"):
            values.setdefault("auth", {})["database"] = service.environment["POSTGRES_DB"]
        if service.environment.get("POSTGRES_USER"):
            values.setdefault("auth", {})["username"] = service.environment["POSTGRES_USER"]
        if service.environment.get("POSTGRES_PASSWORD"):
            values.setdefault("auth", {})["password"] = service.environment["POSTGRES_PASSWORD"]
        return Resolution(
            "known-service",
            self.chart,
            self.repository,
            self.chart_version,
            values,
            ["Persistence is disabled for generated smoke/control-plane adaptations; review state and credentials before production use."],
            chart_digest=self.chart_digest,
            images=(self.postgres, self.exporter, self.os_shell),
        )


class RedisResolver(_ImagePrefixResolver):
    image_names = ("redis",)
    chart = "bitnami/redis"
    repository = "https://charts.bitnami.com/bitnami"
    chart_version = "28.3.1"
    chart_digest = "sha256:4dacf5a4f67aca6d1565b0bb9fcd0343b22237efd14621cd47c0598f747c1092"
    redis = ImageMaterial(
        "redis-image",
        "docker.io/bitnamilegacy/redis",
        "8.2.1-debian-12-r0",
        "sha256:25bf63f3caf75af4628c0dfcf39859ad1ac8abe135be85e99699f9637b16dc28",
    )
    sentinel = ImageMaterial(
        "redis-sentinel-image",
        "docker.io/bitnamilegacy/redis-sentinel",
        "8.2.1-debian-12-r0",
        "sha256:0ca3ea1d2f823c2d9265e0d9e682dc435f219f8d3385aed75b5bb0f365f516a9",
        required=False,
    )
    exporter = ImageMaterial(
        "redis-exporter-image",
        "docker.io/bitnamilegacy/redis-exporter",
        "1.76.0-debian-12-r0",
        "sha256:d111b8a14d96f7edd67324776d6801b76023035d9390d03fbb13d1c21bda8b88",
        required=False,
    )
    kubectl = ImageMaterial(
        "kubectl-image",
        "docker.io/bitnamilegacy/kubectl",
        "1.33.4-debian-12-r0",
        "sha256:ed0b31a0508da84ee655c5c6e01bd3897fc56ad6cf69debb27fa1893a06d2246",
        required=False,
    )
    os_shell = ImageMaterial(
        "os-shell-image",
        "docker.io/bitnamilegacy/os-shell",
        "12-debian-12-r51",
        "sha256:77e65e9d633ec1463f8bea185763aa7ef91e5ddbe0b60beb1b0b5d4da58882b6",
        required=False,
    )

    def resolve(self, service: Service) -> Resolution:
        values = {
            "global": {"security": {"allowInsecureImages": True}},
            "fullnameOverride": service.name,
            "image": _image_values(self.redis.repository, self.redis.version, self.redis.digest),
            "architecture": "standalone",
            "auth": {
                "enabled": False,
            },
            "master": {
                "persistence": {
                    "enabled": False,
                },
            },
            "sentinel": {
                "image": _image_values(self.sentinel.repository, self.sentinel.version, self.sentinel.digest),
            },
            "metrics": {
                "image": _image_values(self.exporter.repository, self.exporter.version, self.exporter.digest),
            },
            "kubectl": {
                "image": _image_values(self.kubectl.repository, self.kubectl.version, self.kubectl.digest),
            },
            "volumePermissions": {
                "image": _image_values(self.os_shell.repository, self.os_shell.version, self.os_shell.digest),
            },
            "sysctl": {
                "image": _image_values(self.os_shell.repository, self.os_shell.version, self.os_shell.digest),
            },
        }
        return Resolution(
            "known-service",
            self.chart,
            self.repository,
            self.chart_version,
            values,
            ["Persistence is disabled for generated smoke adaptations; review state and credentials before production use."],
            chart_digest=self.chart_digest,
            images=(self.redis, self.sentinel, self.exporter, self.kubectl, self.os_shell),
        )


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
