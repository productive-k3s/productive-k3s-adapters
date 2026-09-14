from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from productive_k3s_adapters.model import Application, Service
from productive_k3s_adapters.resolvers import resolve_service
from productive_k3s_adapters.resolvers.base import Resolution
from productive_k3s_adapters.targets.yamlio import write_yaml


def _repo_alias(resolution: Resolution) -> str:
    if resolution.chart.startswith("stakater/"):
        return "stakater"
    if resolution.chart.startswith("bitnami/"):
        return "bitnami"
    if resolution.chart.startswith("minio/"):
        return "minio"
    return re.sub(r"[^a-z0-9-]+", "-", resolution.chart.split("/", 1)[0].lower())


def _write_script(path: Path, content: str) -> None:
    path.write_text(content)
    path.chmod(0o755)


def _addon_descriptor(app: Application, service: Service, resolution: Resolution) -> dict:
    exposure = {}
    if service.ports:
        exposure = {
            "public": {
                "mode": "clusterip",
                "namespace": f"pk3s-{app.name}",
                "service": {
                    "name": service.name,
                    "port": service.ports[0].published or service.ports[0].container,
                },
            }
        }
    spec = {
        "type": "helm",
        "impact": {
            "cluster": True,
            "host": False,
            "summary": f"Generated component '{service.name}' from {app.source_type} source.",
        },
        "configure": {"script": "scripts/configure.sh"},
        "install": {"script": "scripts/install.sh"},
        "validate": {"script": "scripts/validate.sh"},
        "clean": {"script": "scripts/clean.sh"},
        "backup": {"script": "scripts/backup.sh"},
    }
    if exposure:
        spec["productiveK3s"] = {"exposure": exposure}
    return {
        "apiVersion": "addons.productive-k3s.io/v1",
        "kind": "Addon",
        "metadata": {"name": f"{app.name}-{service.name}", "version": "0.1.0", "category": "generated"},
        "spec": spec,
    }


def _generate_addon(app: Application, service: Service, resolution: Resolution, addon_dir: Path) -> None:
    scripts = addon_dir / "scripts"
    scripts.mkdir(parents=True)
    write_yaml(addon_dir / "addon.yaml", _addon_descriptor(app, service, resolution))
    write_yaml(addon_dir / "values.yaml", resolution.values)

    alias = _repo_alias(resolution)
    namespace = f"pk3s-{app.name}"
    release = f"{app.name}-{service.name}"
    chart = resolution.chart
    version_arg = f' --version "{resolution.version}"' if resolution.version else ""

    _write_script(
        scripts / "install.sh",
        f'''#!/usr/bin/env bash
set -euo pipefail
ADDON_SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
HELM_BIN="${{PK3S_HELM_BIN:-helm}}"
VALUES_FILE="${{ADDON_SCRIPT_DIR}}/../values.yaml"
RELEASE_NAME="${{PK3S_ADDON_RELEASE_NAME:-{release}}}"
NAMESPACE="${{PK3S_ADDON_NAMESPACE:-{namespace}}}"

pk3s_addon_install() {{
  "${{HELM_BIN}}" repo add {alias} {resolution.repository} >/dev/null 2>&1 || true
  "${{HELM_BIN}}" repo update >/dev/null
  "${{HELM_BIN}}" upgrade --install "${{RELEASE_NAME}}" {chart}{version_arg} \\
    --namespace "${{NAMESPACE}}" \\
    --create-namespace \\
    -f "${{VALUES_FILE}}"
}}

if [[ "${{BASH_SOURCE[0]}}" == "$0" ]]; then pk3s_addon_install "$@"; fi
''',
    )
    _write_script(
        scripts / "configure.sh",
        '''#!/usr/bin/env bash
set -euo pipefail
pk3s_addon_configure() { :; }
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then pk3s_addon_configure "$@"; fi
''',
    )
    _write_script(
        scripts / "validate.sh",
        f'''#!/usr/bin/env bash
set -euo pipefail
HELM_BIN="${{PK3S_HELM_BIN:-helm}}"
RELEASE_NAME="${{PK3S_ADDON_RELEASE_NAME:-{release}}}"
NAMESPACE="${{PK3S_ADDON_NAMESPACE:-{namespace}}}"
pk3s_addon_validate() {{ "${{HELM_BIN}}" status "${{RELEASE_NAME}}" -n "${{NAMESPACE}}" >/dev/null; }}
if [[ "${{BASH_SOURCE[0]}}" == "$0" ]]; then pk3s_addon_validate "$@"; fi
''',
    )
    _write_script(
        scripts / "clean.sh",
        f'''#!/usr/bin/env bash
set -euo pipefail
HELM_BIN="${{PK3S_HELM_BIN:-helm}}"
RELEASE_NAME="${{PK3S_ADDON_RELEASE_NAME:-{release}}}"
NAMESPACE="${{PK3S_ADDON_NAMESPACE:-{namespace}}}"
pk3s_addon_clean() {{ "${{HELM_BIN}}" uninstall "${{RELEASE_NAME}}" -n "${{NAMESPACE}}" || true; }}
if [[ "${{BASH_SOURCE[0]}}" == "$0" ]]; then pk3s_addon_clean "$@"; fi
''',
    )
    _write_script(
        scripts / "backup.sh",
        '''#!/usr/bin/env bash
set -euo pipefail
pk3s_addon_backup() {
  echo "No generic backup strategy was generated. Configure backup explicitly for stateful components." >&2
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then pk3s_addon_backup "$@"; fi
''',
    )
    (addon_dir / "README.md").write_text(
        f"# {service.name}\n\nGenerated Productive K3s add-on.\n\n"
        f"Resolver: `{resolution.kind}`  \nChart: `{resolution.chart}`\n"
    )


def generate_stack(app: Application, output: str | Path, force: bool = False) -> Path:
    target = Path(output)
    if target.exists():
        if not force:
            raise FileExistsError(f"Output already exists: {target}. Use --force to replace it.")
        shutil.rmtree(target)
    target.mkdir(parents=True)
    (target / "addons").mkdir()

    stack_addons = []
    report = {"application": app.name, "source": app.source_file, "components": []}

    for service in app.services:
        resolution = resolve_service(service)
        addon_path = Path("addons") / service.name
        _generate_addon(app, service, resolution, target / addon_path)
        item = {"name": service.name, "path": str(addon_path)}
        if service.depends_on:
            item["dependsOn"] = service.depends_on
        stack_addons.append(item)
        report["components"].append(
            {
                "name": service.name,
                "image": service.image,
                "resolution": resolution.kind,
                "chart": resolution.chart,
                "notes": resolution.notes,
                "reviewRequired": {
                    "volumes": [v.target for v in service.volumes],
                    "chartVersionPinned": bool(resolution.version),
                },
            }
        )

    stack = {
        "apiVersion": "stacks.productive-k3s.io/v1alpha1",
        "kind": "Stack",
        "metadata": {"name": app.name, "version": "0.1.0"},
        "spec": {
            "generatedBy": "productive-k3s-adapters",
            "source": {"type": app.source_type, "file": app.source_file},
            "addons": stack_addons,
        },
    }
    write_yaml(target / "stack.yaml", stack)
    (target / "conversion-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (target / "README.md").write_text(
        f"# {app.name}\n\nGenerated by Productive K3s Adapters.\n\n"
        "Each component under `addons/` follows the current Productive K3s Addon contract. "
        "Review `conversion-report.json`, persistence, credentials, chart versions and the "
        "v1alpha1 Stack descriptor before catalog publication.\n"
    )
    return target
