# Release

This project publishes the `noc-living-docs` Python package to PyPI. After a successful PyPI release, users can install the CLI with:

```bash
pipx install noc-living-docs
```

Until the PyPI project is published, use the source install path:

```bash
pipx install git+https://github.com/SmallNoc/noc-living-docs.git
```

## Local Release Checks

Run these checks before creating a release tag:

```bash
python -m pip install --upgrade pip build twine pytest
python -m unittest tests.test_noc_cli tests.test_release_cli
pytest
python scripts/noc.py validate
python scripts/release.py --check
python -m py_compile scripts/noc.py scripts/init-noc-docs.py scripts/index-noc-docs.py scripts/release.py scripts/validate-noc-docs.py
python -m build
python -m twine check dist/*
```

Confirm that `dist/` contains both files:

```text
noc_living_docs-<version>-py3-none-any.whl
noc_living_docs-<version>.tar.gz
```

Also verify the built wheel installs and exposes the CLI:

```bash
python -m pip install --force-reinstall dist/noc_living_docs-<version>-py3-none-any.whl
noc --help
noc init /tmp/noc-publish-check
test -f /tmp/noc-publish-check/noc_docs/.living-docs/config.json
```

## Version Checklist

Before tagging, confirm the release version is consistent in:

- `pyproject.toml`
- `VERSION`
- `CHANGELOG.md`
- `README.md`

The tag must match the version with a `v` prefix, for example `v1.0.2`.

## PyPI Trusted Publishing

This repository uses PyPI Trusted Publishing through GitHub Actions. Do not put a PyPI token, password, or API key in code, README, workflow files, issue comments, or chat.

Set up the trusted publisher manually in PyPI:

1. Log in to PyPI.
2. Open the `noc-living-docs` project.
3. Go to Publishing / Trusted Publishers.
4. Add a GitHub Actions publisher with:
   - Owner: `SmallNoc`
   - Repository: `noc-living-docs`
   - Workflow filename: `publish.yml`
   - Environment: `pypi`
   - Project name: `noc-living-docs`

The workflow is `.github/workflows/publish.yml`. It runs when a tag like `v1.0.2` is pushed, builds the package, uploads `dist/` as a workflow artifact, and publishes to PyPI through OIDC.

## Release Flow

After local checks pass and PyPI Trusted Publishing is configured:

```bash
git tag v1.0.2
git push origin v1.0.2
```

Watch the `Publish to PyPI` workflow. After it succeeds, verify:

```bash
pipx install noc-living-docs
noc --help
```
