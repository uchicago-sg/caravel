#!/bin/bash -e
#
# This script updates the contents of vendor/ from requirements.txt.

rm -rf vendor/ venv/

# Grab packages.
virtualenv venv/
. venv/bin/activate
pip install -r requirements.txt

# Copy into vendor/.
cp -R venv/lib/python*/site-packages vendor/

# Clean up non-source files.
rm -Rf vendor/*.{egg,dist}-info venv/ vendor/{easy_install,pip,pkg_resources}* 
find vendor/ -name '*.pyc' | xargs rm -Rf
