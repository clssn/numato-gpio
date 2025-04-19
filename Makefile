.PHONY: curl uv format check usage test sys-test coverage browse-coverage clean extraclean setup
usage:
	@echo ""
	@echo "Project maintenance targets:"
	@echo ""
	@echo "  setup       Install pre-commit hook"
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

setup: uv
	uvx pre-commit install

git:
	@which git > /dev/null || (echo "You need to install for this command to work." && exit 1)

test: uv
	find tests -name "test*.py" -exec uv run pytest {} \;

sys-test: uv
	find sys_tests -name "test*.py" -exec uv run pytest {} \;

coverage: uv
	uv run pytest --cov=src --cov-report=html:doc/htmlcov tests

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
