#!/bin/bash -e

if ! [ -d venv/ ]; then
	virtualenv venv/
	source venv/bin/activate
	pip install -U -r requirements_dev.txt
else
	source venv/bin/activate
fi

nose2 --log-capture --plugin nose2.plugins.doctests --with-doctest
