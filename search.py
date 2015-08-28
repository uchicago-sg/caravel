import models

from google.appengine.ext import db

def lookup_listing(permalink):
    return models.Listing.get_by_key_name(permalink)

def run_query(query):
    return models.Listing.all().order("posting_time")
