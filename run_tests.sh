#!/bin/bash -ex -o pipefail
#
# Runs all tests.

if ! [ -d dev_venv ]; then
	virtualenv dev_venv
fi

. dev_venv/bin/activate
pip install -r requirements_dev.txt
coverage run --source=caravel $(which nose2) --log-capture \
	--plugin nose2.plugins.doctests --with-doctest
coverage report