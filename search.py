import models

def run_query(query):
    return models.Listing.all().order("-posting_time")