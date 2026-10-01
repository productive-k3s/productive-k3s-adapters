import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import yaml

from productive_k3s_adapters.adapters.compose.parser import ComposeError, parse_compose
from productive_k3s_adapters.cli import _application, main
from productive_k3s_adapters.model import Application, Port, Service, Volume
from productive_k3s_adapters.resolvers import resolve_service
from productive_k3s_adapters.resolvers.base import Resolver, image_repository_and_tag
from productive_k3s_adapters.stack import generate_stack


class ParserBehaviorTests(unittest.TestCase):
    def write_compose(self, directory: str, services) -> Path:
        path = Path(directory) / "compose.yaml"
        path.write_text(yaml.safe_dump({"services": services}))
        return path

    def test_normalizes_supported_compose_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_compose(
                tmp,
                {
                    "app": {
                        "image": "registry.example:5000/team/app:1.2.3",
                        "command": "run --foreground",
                        "environment": ["EMPTY", "COUNT=2"],
                        "ports": [8080, "127.0.0.1:9090:90/udp", {"target": 3000, "published": 80}],
                        "volumes": ["/cache", "data:/data:ro", {"source": "cfg", "target": "/cfg", "read_only": True}],
                        "depends_on": {"db": {"condition": "service_started"}},
                        "deploy": {"replicas": 3},
                    },
                    "db": {"image": "postgres@sha256:abc", "environment": {"POSTGRES_DB": None}},
                },
            )
            app = parse_compose(path)

        service = app.services[0]
        self.assertEqual(app.name, Path(tmp).name)
        self.assertEqual(service.command, ["/bin/sh", "-c", "run --foreground"])
        self.assertEqual(service.environment, {"EMPTY": "", "COUNT": "2"})
        self.assertEqual([(p.container, p.published, p.protocol) for p in service.ports], [(8080, None, "TCP"), (90, 9090, "UDP"), (3000, 80, "TCP")])
        self.assertEqual(service.depends_on, ["db"])
        self.assertEqual(service.replicas, 3)
        self.assertEqual(service.volumes[0], Volume(None, "/cache"))
        self.assertTrue(service.volumes[1].read_only)
        self.assertTrue(service.volumes[2].read_only)
        self.assertEqual(app.services[1].environment, {"POSTGRES_DB": ""})

    def test_rejects_invalid_sources_and_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(ComposeError, "does not exist"):
                parse_compose(root / "missing.yaml")
            for services, message in [
                ({}, "at least one service"),
                ({"app": {"build": "."}}, "requires a built image"),
                ({"app": {}}, "does not define image"),
                ({"app": {"image": "app", "environment": 4}}, "environment"),
                ({"app": {"image": "app", "command": {"bad": True}}}, "command"),
                ({"app": {"image": "app", "ports": [{"published": 80}]}}, "missing target"),
                ({"app": {"image": "app", "volumes": [{"source": "data"}]}}, "missing target"),
            ]:
                path = self.write_compose(tmp, services)
                with self.assertRaisesRegex(ComposeError, message):
                    parse_compose(path)


class ResolverBehaviorTests(unittest.TestCase):
    def test_image_identity_variants(self):
        self.assertEqual(image_repository_and_tag("app"), ("app", None))
        self.assertEqual(image_repository_and_tag("registry:5000/app:1"), ("registry:5000/app", "1"))
        self.assertEqual(image_repository_and_tag("app@sha256:abc"), ("app", "sha256:abc"))

    def test_known_resolvers_map_configuration(self):
        postgres = resolve_service(Service("db", "postgres:16", environment={"POSTGRES_DB": "app", "POSTGRES_USER": "user", "POSTGRES_PASSWORD": "secret"}))
        self.assertEqual(postgres.values["auth"], {"database": "app", "username": "user", "password": "secret"})
        minio = resolve_service(Service("objects", "quay.io/minio/minio:latest", environment={"MINIO_ROOT_USER": "root", "MINIO_ROOT_PASSWORD": "secret"}))
        self.assertEqual(minio.values, {"rootUser": "root", "rootPassword": "secret"})

    def test_generic_resolver_preserves_runtime_inputs(self):
        service = Service("web", "app@sha256:abc", command=["serve"], environment={"B": "2", "A": "1"}, ports=[Port(8080, 80, "TCP")], volumes=[Volume("data", "/data")], replicas=2)
        resolution = resolve_service(service)
        deployment = resolution.values["deployment"]
        self.assertEqual(deployment["image"]["digest"], "sha256:abc")
        self.assertEqual(deployment["command"], ["serve"])
        self.assertEqual(list(deployment["env"]), ["A", "B"])
        self.assertEqual(resolution.values["service"]["ports"][0]["port"], 80)
        self.assertTrue(resolution.notes)

    def test_base_resolver_is_abstract_by_contract(self):
        resolver = Resolver()
        with self.assertRaises(NotImplementedError):
            resolver.matches(Service("app", "app"))
        with self.assertRaises(NotImplementedError):
            resolver.resolve(Service("app", "app"))


class CliBehaviorTests(unittest.TestCase):
    def compose(self, directory: str) -> Path:
        path = Path(directory) / "compose.yaml"
        path.write_text("services:\n  app:\n    image: example/app:1\n    ports: [8080]\n")
        return path

    def invoke(self, argv):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(argv)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_validate_inspect_and_convert(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.compose(tmp)
            status, output, _ = self.invoke(["validate", "compose", str(source)])
            self.assertEqual(status, 0)
            self.assertIn("1 services", output)

            status, output, _ = self.invoke(["inspect", "compose", str(source), "--name", "demo"])
            self.assertEqual(status, 0)
            self.assertEqual(json.loads(output)["services"][0]["resolver"], "generic-application")

            target = Path(tmp) / "generated"
            status, output, _ = self.invoke(["convert", "compose", str(source), "-o", str(target)])
            self.assertEqual(status, 0)
            self.assertEqual(Path(output.strip()), target)
            status, _, error = self.invoke(["convert", "compose", str(source), "-o", str(target)])
            self.assertEqual(status, 2)
            self.assertIn("Use --force", error)
            status, _, _ = self.invoke(["convert", "compose", str(source), "-o", str(target), "--force"])
            self.assertEqual(status, 0)

    def test_cli_reports_parse_failures(self):
        status, _, error = self.invoke(["validate", "compose", "/missing/compose.yaml"])
        self.assertEqual(status, 2)
        self.assertIn("ERROR:", error)
        with self.assertRaisesRegex(ValueError, "Unsupported adapter"):
            _application("unknown", "source", None)


class GeneratorBehaviorTests(unittest.TestCase):
    def test_generated_digest_material_and_unknown_chart_alias(self):
        app = Application(
            name="demo",
            services=[Service("web", "example/app@sha256:abc", ports=[Port(8080)])],
            source_type="test",
            source_file="fixture",
        )
        with tempfile.TemporaryDirectory() as tmp:
            target = generate_stack(app, Path(tmp) / "out")
            lock = yaml.safe_load((target / "addons/web/materials.lock.yaml").read_text())
            image = lock["spec"]["materials"][1]
            self.assertEqual(image["digest"], "sha256:abc")
            self.assertEqual(image["pinPolicy"], "exact-digest")


if __name__ == "__main__":
    unittest.main()
