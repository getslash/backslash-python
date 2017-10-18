default: test

test: env
	.env/bin/py.test -x tests --cov=backslash --cov-report=html

doc: env
	.env/bin/python setup.py build_sphinx -a -E

env: .env/.up-to-date


.env/.up-to-date: setup.py Makefile setup.cfg
	virtualenv --no-site-packages .env
	.env/bin/pip install -e .[testing]
	touch $@

