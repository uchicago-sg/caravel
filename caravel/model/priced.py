from google.appengine.ext import ndb


class FixedPoint(ndb.IntegerProperty):

    def _validate(self, value):
        int(value)

    def _to_base_type(self, value):
        return int(round(value * 100))

    def _from_base_type(self, value):
        return value / 100.


class PriceMixin(ndb.Model):

    """
    The PriceMixin adds a price to the given entity.

    >>> class D(PriceMixin): pass
    >>> x = D()
    >>> x.price = 3.234444
    >>> key = x.put()
    >>> x.price
    3.23
    """

    price = FixedPoint(default=0)
