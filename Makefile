.PHONY: usage test sys-test coverage browse-coverage release clean
usage:
	@echo ""
	@echo "Project mainentance targets:"
	@echo ""
	@echo "  deps      Install maintenance dependencies"
	@echo "  build     Build the numato-gpio wheel"
	@echo "  release   Push the wheel to PyPI"
	@echo "  clean     Remove all wheels"
	@echo ""

.env:
	virtualenv .env
	. .env/bin/activate && python3 -m pip freeze > requirements-venv.txt
	. .env/bin/activate && python3 -m pip install -e .
	. .env/bin/activate && python3 -m pip freeze | grep -v numato_gpio > requirements-all.txt
	. .env/bin/activate && cat requirements-all.txt | grep -Fvf requirements-venv.txt > requirements.txt
	. .env/bin/activate && python3 -m pip install -r requirements-dev.txt -r requirements.txt
	rm requirements-all.txt requirements-venv.txt

test: .env
	pytest -v tests

sys-test: .env
	pytest sys_tests

coverage: .env
	pytest --cov=src --cov-report=html:doc/htmlcov tests

browse-coverage: coverage
	python3 -m webbrowser -t ${PWD}/doc/htmlcov/index.html


release: .env build
	python3 setup.py sdist bdist_wheel
	python3 -m twine upload dist/*

clean:
	rm -rf build dist .env .tox doc/htmlcov
