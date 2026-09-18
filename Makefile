.PHONY: install install-dev validate validate-adaptation convert-example convert-adaptation inspect-adaptation smoke-adaptation adaptations-build test lint docs-build docs-serve docs-up docs-down clean tag-release

PYTHON ?= python3
PYTHONPATH ?= src
ADAPTATION ?= adaptations/openship/whoami-redis
ADAPTATION_NAME ?= openship-whoami-redis

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e '.[dev,docs]'

validate: validate-adaptation smoke-adaptation

validate-adaptation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m productive_k3s_adapters.cli validate compose $(ADAPTATION)/compose.yaml

convert-example: convert-adaptation

convert-adaptation:
	rm -rf .generated/adaptations/openship/whoami-redis/source
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m productive_k3s_adapters.cli convert compose $(ADAPTATION)/compose.yaml --name $(ADAPTATION_NAME) --output .generated/adaptations/openship/whoami-redis/source

inspect-adaptation:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m productive_k3s_adapters.cli inspect compose $(ADAPTATION)/compose.yaml

smoke-adaptation: adaptations-build
	test -f .generated/adaptations/openship/whoami-redis/source/stack.yaml
	test -f .generated/adaptations/openship/whoami-redis/source/conversion-report.json
	test -f .generated/adaptations/openship/whoami-redis/source/addons/web/values.yaml
	test -f .generated/adaptations/openship/whoami-redis/source/addons/cache/values.yaml
	test -f .generated/adaptations/openship/whoami-redis/package/stack.yaml
	test -f .generated/adaptations/openship/whoami-redis/package/addons/openship-whoami-redis-web-0.1.0.tgz
	test -f .generated/adaptations/openship/whoami-redis/package/addons/openship-whoami-redis-cache-0.1.0.tgz
	test -f .generated/adaptations/openship/whoami-redis/openship-whoami-redis-0.1.0.tgz

adaptations-build:
	PYTHON=$(PYTHON) OUTPUT_DIR=.generated/adaptations ./scripts/build-adaptations.sh

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m unittest discover -s tests -v

lint:
	PYTHONPATH=$(PYTHONPATH) ruff check src tests

docs-build:
	$(MAKE) -C ./docs docs-build

docs-serve:
	$(MAKE) -C ./docs docs-serve

docs-up:
	$(MAKE) -C ./docs docs-up

docs-down:
	$(MAKE) -C ./docs docs-down

clean:
	rm -rf .generated build dist *.egg-info src/*.egg-info
	$(MAKE) -C ./docs docs-clean

tag-release:
	./scripts/create-release-tag.sh $(VERSION)
