default: test

test: env
	.env/bin/pytest -x tests --cov=backslash --cov-report=html

pylint: env
	.env/bin/pylint --rcfile .pylintrc backslash tests

doc: env
	.env/bin/sphinx-build -a -W -E docs build/sphinx/html

env: .env/.up-to-date


.env/.up-to-date: setup.py Makefile setup.cfg
	python3 -m venv .env
	.env/bin/pip install -e .[testing,doc]
	touch $@

