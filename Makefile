.PHONY: install install-dev validate convert-example inspect-example test lint docs-build docs-serve clean tag-release

install:
	python -m pip install -e .

install-dev:
	python -m pip install -e '.[dev,docs]'

validate:
	python -m productive_k3s_adapters.cli validate compose examples/openship/compose.yaml

convert-example:
	rm -rf .generated/openship-demo
	python -m productive_k3s_adapters.cli convert compose examples/openship/compose.yaml --name openship-demo --output .generated/openship-demo

inspect-example:
	python -m productive_k3s_adapters.cli inspect compose examples/openship/compose.yaml

test:
	python -m unittest discover -s tests -v

lint:
	ruff check src tests

docs-build:
	$(MAKE) -C ./docs docs-build

docs-serve:
	$(MAKE) -C ./docs docs-serve

clean:
	rm -rf .generated build dist *.egg-info src/*.egg-info
	$(MAKE) -C ./docs docs-clean

tag-release:
	./scripts/create-release-tag.sh $(VERSION)
