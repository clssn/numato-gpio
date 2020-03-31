.PHONY: build release

update-deps:
	python3 -m pip install --user --upgrade twine setuptools wheel

build: update-deps
	python3 setup.py sdist bdist_wheel

release: build
	python3 -m twine upload dist/*