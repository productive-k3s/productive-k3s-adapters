from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from productive_k3s_adapters import __version__
from productive_k3s_adapters.adapters.compose import parse_compose
from productive_k3s_adapters.resolvers import resolve_service
from productive_k3s_adapters.stack import generate_stack


def _application(source_type: str, path: str, name: str | None):
    if source_type != "compose":
        raise ValueError(f"Unsupported adapter: {source_type}")
    return parse_compose(path, name=name)


def _inspect(app) -> dict:
    return {
        "name": app.name,
        "sourceType": app.source_type,
        "services": [
            {
                "name": service.name,
                "image": service.image,
                "resolver": resolve_service(service).kind,
                "chart": resolve_service(service).chart,
                "ports": [p.container for p in service.ports],
                "dependsOn": service.depends_on,
            }
            for service in app.services
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pk3s-adapters", description="Convert external app definitions into Productive K3s artifacts")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for command in ("validate", "inspect"):
        p = sub.add_parser(command)
        p.add_argument("adapter", choices=["compose"])
        p.add_argument("source")
        p.add_argument("--name")

    convert = sub.add_parser("convert")
    convert.add_argument("adapter", choices=["compose"])
    convert.add_argument("source")
    convert.add_argument("--name")
    convert.add_argument("--output", "-o", required=True)
    convert.add_argument("--force", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        app = _application(args.adapter, args.source, getattr(args, "name", None))
        if args.command == "validate":
            print(f"OK: {args.source} ({len(app.services)} services)")
            return 0
        if args.command == "inspect":
            print(json.dumps(_inspect(app), indent=2))
            return 0
        if args.command == "convert":
            target = generate_stack(app, args.output, force=args.force)
            print(target)
            return 0
    except Exception as exc:  # CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
