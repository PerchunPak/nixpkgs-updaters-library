SHELL:=/usr/bin/env bash

.PHONY: format
format:
	black .
	isort .
	pycln .

.PHONY: lint
lint:
	mypy .

.PHONY: style
style: format lint

.PHONY: unit
unit:
	pytest

.PHONY: package
package:
	poetry check
	pip check

.PHONY: test
test: style package unit
