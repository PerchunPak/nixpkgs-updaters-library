SHELL:=/usr/bin/env bash

.PHONY: test
test:
	ruff check --fix .
	ruff format .
	basedpyright .
	pytest .
