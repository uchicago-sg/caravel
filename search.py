import models

def run_query(query):
    return models.Listing.query().order(models.Listing.posted_at)