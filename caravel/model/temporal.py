from google.appengine.ext import ndb
import datetime


class TimeOrderMixin(ndb.Model):

    """
    The TimeOrderMixin defines entities that have a creation time.
    """

    posted_at = ndb.DateTimeProperty()

    @property
    def old(self):
        return self.age >= self.MARK_AS_OLD_AFTER

    @property
    def age(self):
        return datetime.datetime.now() - self.posted_at
