.PHONY: usage test sys-test coverage browse-coverage clean
usage:
	@echo ""
	@echo "Project maintenance targets:"
	@echo ""
	@echo "  test      Run all unit-tests"
	@echo "  sys-test  Run all system-tests (with a device connected)"
	@echo "  release   Author a release commit and create the tag"
	@echo "  clean     Remove all files not under version control"
	@echo ""

test:
	poetry run pytest -n $(shell nproc) tests

sys-test:
	poetry run pytest -n 1 sys_tests

coverage:
	poetry run pytest -n $(shell nproc) --cov=src --cov-report=html:doc/htmlcov tests

browse-coverage: coverage
	poetry run python3 -m http.server -d ${PWD}/doc/htmlcov 8080


clean:
	git clean -df
