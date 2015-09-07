#!/usr/bin/env python

import sys

URLs = ["/_integration_test",
        "/?q=sublet",
        "/listing-a"]

import subprocess, time, urllib2
dev_appserver = subprocess.Popen([
    "dev_appserver.py",
    "--port", "4143",
    "--admin_port", "4142",
    "--clear_datastore", "true",
    "--require_indexes", "true",
    "--skip_sdk_update_check", "true",
    "."])

try:
    time.sleep(5)

    for url in URLs:
        result = urllib2.urlopen("http://localhost:4143" + url)
        if result.getcode() != 200:
            print "Unable to GET {}: HTTP {}".format(url, result.getcode())
            sys.exit(1)

finally:
    dev_appserver.terminate()
    dev_appserver.wait()