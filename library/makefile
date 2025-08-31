build:
	pip3 install build twine
	python3 -m build
set:
vi ~/.pypirc
[pypi]
username = __token__
twine:
	python3 -m twine upload dist/*
install:
	pip install --index-url https://user:password@your-private-repo/simple/ trading-core
