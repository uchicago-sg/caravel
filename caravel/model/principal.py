from google.appengine.ext import ndb
from caravel.utils import Principal

def validator(_, value):
    if not isinstance(value, Principal):
        raise TypeError(value)
    return value

class PrincipalMixin(ndb.Model):
    """
    A PrincipalMixin allows an entity to be associated to a person. This usually
    indicates the person that initiated an action.
    """

    principal = ndb.PickleProperty(validator=validator)
