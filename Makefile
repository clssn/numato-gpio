.PHONY: poetry usage test sys-test coverage browse-coverage clean extraclean
usage:
	@echo ""
	@echo "Project maintenance targets:"
	@echo ""
	@echo "  test        Run all unit-tests"
	@echo "  sys-test    Run all system-tests (with a device connected)"
	@echo "  release     Author a release commit and create the tag"
	@echo "  clean       Remove all non-git-ignored files not under version control"
	@echo "  extraclean  Remove all files not under version control"
	@echo ""

poetry:
	@which poetry > /dev/null || (echo "You need to "pip install poetry" for this command to work." && exit 1)

git:
	@which git > /dev/null || (echo "You need to install for this command to work." && exit 1)

test: poetry
	poetry run pytest -n $(shell nproc) tests

sys-test: poetry
	poetry run pytest -n 1 sys_tests

coverage: poetry
	poetry run pytest -n $(shell nproc) --cov=src --cov-report=html:doc/htmlcov tests

browse-coverage: coverage poetry
	poetry run python3 -m http.server -d ${PWD}/doc/htmlcov 8080

clean: git
	git clean -df

extraclean: git
	git clean -dxf