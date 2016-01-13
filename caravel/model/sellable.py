from google.appengine.ext import ndb


class SellableMixin(ndb.Model):
    sold = ndb.BooleanProperty(default=False)
