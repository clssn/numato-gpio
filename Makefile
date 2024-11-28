.PHONY: curl uv format check usage test sys-test coverage browse-coverage clean extraclean
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

curl:
	@which curl > /dev/null || (echo "Install curl in order to be able to install uv." && exit 1)

uv: curl
	@which uv > /dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

git:
	@which git > /dev/null || (echo "You need to install for this command to work." && exit 1)

test: uv
	uv run pytest -n $(shell nproc) tests

sys-test: uv
	uv run pytest -n 1 sys_tests

coverage: uv
	uv run pytest -n $(shell nproc) --cov=src --cov-report=html:doc/htmlcov tests

browse-coverage: coverage uv
	uv run python3 -m http.server -d ${PWD}/doc/htmlcov 8080

format:
	uvx ruff format

check:
	uvx ruff check --select=ALL

clean: git
	git clean -df

extraclean: git
	git clean -dxf
