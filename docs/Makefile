.PHONY: docs-build docs-serve docs-up docs-down docs-clean sync-theme

docs-build: sync-theme
	./build.sh

docs-serve: sync-theme
	./serve.sh

docs-up: sync-theme
	./serve.sh --background

docs-down:
	./clean.sh

docs-clean:
	./clean.sh

sync-theme:
	./sync-shared-theme.sh
