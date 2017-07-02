default: test

test: env
	.env/bin/py.test -x tests --cov=backslash --cov-report=html

doc: env
	.env/bin/python setup.py build_sphinx -a -E

env: .env/.up-to-date


.env/.up-to-date: setup.py Makefile test_requirements.txt
	virtualenv --no-site-packages .env
	.env/bin/pip install -e .
	.env/bin/pip install -r ./*.egg-info/requires.txt || true
	.env/bin/pip install -r ./docs/requirements.txt
	.env/bin/pip install -r test_requirements.txt
	touch $@

