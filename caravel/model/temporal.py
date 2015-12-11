from google.appengine.ext import ndb

class TimeOrderMixin(ndb.Model):
    """
    The TimeOrderMixin defines entities that have a creation time.
    """

    posted_at = ndb.DateTimeProperty(auto_now_add=True)
