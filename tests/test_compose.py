import tempfile
import unittest
from pathlib import Path

import yaml

from productive_k3s_adapters.adapters.compose import parse_compose
from productive_k3s_adapters.resolvers import resolve_service
from productive_k3s_adapters.stack import generate_stack

ROOT = Path(__file__).resolve().parents[1]
SMOKE_COMPOSE = ROOT / "adaptations/openship/whoami-redis/compose.yaml"
UPTIME_KUMA_COMPOSE = ROOT / "adaptations/docker-compose/uptime-kuma/compose.yaml"


class ComposeTests(unittest.TestCase):
    def test_parse_and_resolve(self):
        app = parse_compose(SMOKE_COMPOSE, name="demo")
        self.assertEqual(app.name, "demo")
        self.assertEqual(len(app.services), 2)
        by_name = {s.name: s for s in app.services}
        self.assertEqual(resolve_service(by_name["cache"]).chart, "bitnami/redis")
        self.assertEqual(resolve_service(by_name["cache"]).version, "28.3.1")
        self.assertEqual(resolve_service(by_name["cache"]).values["fullnameOverride"], "cache")
        self.assertFalse(resolve_service(by_name["cache"]).values["master"]["persistence"]["enabled"])
        self.assertEqual(resolve_service(by_name["cache"]).values["image"]["repository"], "bitnamilegacy/redis")
        self.assertEqual(resolve_service(by_name["web"]).chart, "stakater/application")
        self.assertEqual(resolve_service(by_name["web"]).version, "9.3.2")
        self.assertFalse(resolve_service(by_name["web"]).values["deployment"]["containerSecurityContext"]["runAsNonRoot"])
        self.assertEqual(by_name["web"].depends_on, ["cache"])
        self.assertEqual(by_name["web"].ports[0].container, 80)
        self.assertEqual(by_name["web"].ports[0].published, 8080)

        control_plane = parse_compose(ROOT / "adaptations/openship/control-plane/compose.yaml")
        api = next(service for service in control_plane.services if service.name == "api")
        api_resolution = resolve_service(api)
        self.assertEqual(api_resolution.values["deployment"]["image"]["tag"], "0.6.5")
        self.assertEqual(
            api_resolution.images[0].digest,
            "sha256:b92087209e7a12b70a501b7d4a997ec572cccb14a975d483d34739e3b10cf2af",
        )

    def test_generate(self):
        app = parse_compose(SMOKE_COMPOSE, name="demo")
        with tempfile.TemporaryDirectory() as tmp:
            target = generate_stack(app, Path(tmp) / "out")
            self.assertTrue((target / "stack.yaml").exists())
            self.assertTrue((target / "addons/web/values.yaml").exists())
            self.assertTrue((target / "conversion-report.json").exists())
            self.assertTrue((target / "addons/web/addon.yaml").exists())
            self.assertTrue((target / "addons/web/materials.lock.yaml").exists())
            self.assertTrue((target / "addons/web/scripts/install.sh").exists())
            self.assertTrue((target / "addons/cache/values.yaml").exists())
            stack = yaml.safe_load((target / "stack.yaml").read_text())
            addon = yaml.safe_load((target / "addons/web/addon.yaml").read_text())
            self.assertEqual(stack["metadata"]["sourceRevision"], "development")
            self.assertEqual(stack["spec"]["compatibility"], addon["spec"]["compatibility"])
            self.assertIn("        distros:\n          - k3s", (target / "stack.yaml").read_text())
            self.assertIn("        distros:\n          - k3s", (target / "addons/web/addon.yaml").read_text())
            install_script = (target / "addons/web/scripts/install.sh").read_text()
            self.assertIn('pull "application"', install_script)
            self.assertIn('sha256sum', install_script)

    def test_docker_compose_producer_candidate(self):
        app = parse_compose(UPTIME_KUMA_COMPOSE, name="docker-compose-uptime-kuma")
        self.assertEqual(app.source_type, "docker-compose")
        self.assertEqual(len(app.services), 1)
        service = app.services[0]
        self.assertEqual(service.name, "uptime-kuma")
        self.assertEqual(
            service.image,
            "louislam/uptime-kuma:2@sha256:e88415a90dd2f7efecdbc18de0490aff292764a3ac471531bf1d0481725591bd",
        )
        self.assertEqual(service.ports[0].container, 3001)
        self.assertEqual(service.ports[0].published, 3001)
        self.assertEqual(service.volumes[0].source, "./data")
        self.assertEqual(service.volumes[0].target, "/app/data")

        with tempfile.TemporaryDirectory() as tmp:
            target = generate_stack(app, Path(tmp) / "out")
            self.assertTrue((target / "addons/uptime-kuma/values.yaml").exists())
            report = (target / "conversion-report.json").read_text()
            self.assertIn('"/app/data"', report)


if __name__ == "__main__":
    unittest.main()
