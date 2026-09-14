# Documentation

The documentation follows the same Productive K3s pattern used by Core: MkDocs Material plus the shared `productive-k3s-docs-theme` Git submodule.

```bash
git submodule update --init --recursive
python -m pip install -r docs/requirements.txt
make docs-build
make docs-serve
```
