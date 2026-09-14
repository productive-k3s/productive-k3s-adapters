# First commit bootstrap

This ZIP contains the repository contents, including the `.gitmodules` declaration for the shared Productive K3s documentation theme.

A Git submodule is stored by Git as a special gitlink entry, which cannot be represented by ordinary files in a source ZIP. After extracting into the new repository, register the submodule before the first commit:

```bash
git init                         # omit if the GitHub repository was already cloned
git submodule add -b main git@github.com:productive-k3s/productive-k3s-docs-theme.git .shared/productive-k3s-docs-theme
git add .
git status
```

Then run the local checks:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make test
make validate
make convert-example
```

The submodule commit used by the other Productive K3s repositories at the time this scaffold was assembled was `a5af071774815225f20cc6e992361b65c07f640c`; pin to that revision if exact visual parity is required for the first commit.
