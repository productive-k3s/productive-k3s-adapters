import tempfile
import unittest
from pathlib import Path

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
        self.assertEqual(resolve_service(by_name["cache"]).values["fullnameOverride"], "cache")
        self.assertFalse(resolve_service(by_name["cache"]).values["master"]["persistence"]["enabled"])
        self.assertEqual(resolve_service(by_name["web"]).chart, "stakater/application")
        self.assertFalse(resolve_service(by_name["web"]).values["deployment"]["containerSecurityContext"]["runAsNonRoot"])
        self.assertEqual(by_name["web"].depends_on, ["cache"])
        self.assertEqual(by_name["web"].ports[0].container, 80)
        self.assertEqual(by_name["web"].ports[0].published, 8080)

    def test_generate(self):
        app = parse_compose(SMOKE_COMPOSE, name="demo")
        with tempfile.TemporaryDirectory() as tmp:
            target = generate_stack(app, Path(tmp) / "out")
            self.assertTrue((target / "stack.yaml").exists())
            self.assertTrue((target / "addons/web/values.yaml").exists())
            self.assertTrue((target / "conversion-report.json").exists())
            self.assertTrue((target / "addons/web/addon.yaml").exists())
            self.assertTrue((target / "addons/web/scripts/install.sh").exists())
            self.assertTrue((target / "addons/cache/values.yaml").exists())

    def test_docker_compose_producer_candidate(self):
        app = parse_compose(UPTIME_KUMA_COMPOSE, name="docker-compose-uptime-kuma")
        self.assertEqual(app.source_type, "docker-compose")
        self.assertEqual(len(app.services), 1)
        service = app.services[0]
        self.assertEqual(service.name, "uptime-kuma")
        self.assertEqual(service.image, "louislam/uptime-kuma:2")
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
