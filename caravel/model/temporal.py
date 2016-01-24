from google.appengine.ext import ndb
import datetime


class TimeOrderMixin(ndb.Model):

    """
    The TimeOrderMixin defines entities that have a creation time.
    """

    posted_at = ndb.DateTimeProperty()

    @property
    def old(self):
        horizon = datetime.datetime.now() - self.MARK_AS_OLD_AFTER
        return (self.posted_at <= horizon)
