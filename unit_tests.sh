#!/bin/bash -e

if ! [ -d venv/ ]; then
	virtualenv venv/
	source venv/bin/activate
	pip install -U -r requirements_dev.txt
else
	source venv/bin/activate
fi

CC_TEST_REPORTER_ID=189ccc50fd525bc8cfca2bebf76da4b6051536a23746618cdab6946c14501893 ./test-reporter-latest-darwin-amd64 before-build

coverage run --source=caravel $(which nose2) --log-capture \
	--plugin nose2.plugins.doctests --with-doctest
coverage report
coverage xml

CC_TEST_REPORTER_ID=189ccc50fd525bc8cfca2bebf76da4b6051536a23746618cdab6946c14501893 ./test-reporter-latest-darwin-amd64 after-build --exit-code 0 -t coverage.py
