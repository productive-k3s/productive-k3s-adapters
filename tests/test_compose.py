from pathlib import Path
import tempfile
import unittest

from productive_k3s_adapters.adapters.compose import parse_compose
from productive_k3s_adapters.resolvers import resolve_service
from productive_k3s_adapters.stack import generate_stack


ROOT = Path(__file__).resolve().parents[1]


class ComposeTests(unittest.TestCase):
    def test_parse_and_resolve(self):
        app = parse_compose(ROOT / "examples/openship/compose.yaml", name="demo")
        self.assertEqual(app.name, "demo")
        self.assertEqual(len(app.services), 3)
        by_name = {s.name: s for s in app.services}
        self.assertEqual(resolve_service(by_name["db"]).chart, "bitnami/postgresql")
        self.assertEqual(resolve_service(by_name["cache"]).chart, "bitnami/redis")
        self.assertEqual(resolve_service(by_name["web"]).chart, "stakater/application")

    def test_generate(self):
        app = parse_compose(ROOT / "examples/openship/compose.yaml", name="demo")
        with tempfile.TemporaryDirectory() as tmp:
            target = generate_stack(app, Path(tmp) / "out")
            self.assertTrue((target / "stack.yaml").exists())
            self.assertTrue((target / "addons/web/values.yaml").exists())
            self.assertTrue((target / "conversion-report.json").exists())
            self.assertTrue((target / "addons/web/addon.yaml").exists())
            self.assertTrue((target / "addons/web/scripts/install.sh").exists())


if __name__ == "__main__":
    unittest.main()
