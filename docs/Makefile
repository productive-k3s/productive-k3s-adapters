.PHONY: docs-build docs-serve docs-clean sync-theme

docs-build: sync-theme
	./build.sh

docs-serve: sync-theme
	./serve.sh

docs-clean:
	./clean.sh

sync-theme:
	./sync-shared-theme.sh
