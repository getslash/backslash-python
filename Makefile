default: test

test: env
	.venv/bin/pytest -x tests --cov=backslash --cov-report=html

pylint: env
	.venv/bin/pylint --rcfile .pylintrc backslash tests

doc: env
	.venv/bin/sphinx-build -a -W -E docs build/sphinx/html

env:
	uv venv
	uv pip install -e .[testing,doc]

