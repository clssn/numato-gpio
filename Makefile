.PHONY: usage deps build release clean 

usage:
	@echo ""
	@echo "Project mainentance targets:"
	@echo ""
	@echo "  deps      Install maintenance dependencies"
	@echo "  build     Build the numato-gpio wheel"
	@echo "  release   Push the wheel to PyPI"
	@echo "  clean     Remove all wheels"
	@echo ""

deps:
	python3 -m pip install --user --upgrade twine setuptools wheel

build: deps
	python3 setup.py sdist bdist_wheel

release: build
	python3 -m twine upload dist/*

clean:
	rm -rf build dist