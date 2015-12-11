from google.appengine.ext import ndb
from caravel.model import principal

class ModeratedMixin(ndb.Model):
    """
    A ModeratedMixin allows an entity to change type once the approval property
    is true. If no approved() method is specified, the class defaults to using
    the .principal property.
    
    >>> from google.appengine.ext import ndb
    
    >>> class Parent(ndb.Model): pass
    >>> class A(Parent): pass
    >>> class B(ModeratedMixin, Parent):
    ...   TYPE_ONCE_APPROVED = A
    ...   def approved(self): return True
    ...
    >>> x = B()
    >>> type(x)
    B<>
    >>> key = x.put()
    >>> type(x)
    A<>
    """

    TYPE_ONCE_APPROVED = None

    def _pre_put_hook(self):
        """
        Changes the type of this class if self.approved() is true.
        """

        if self.approved() and self.TYPE_ONCE_APPROVED:

            # Remove the old entity, if one existed.
            if self.key.id():
                self.key.delete()

            # Change the type of this class.
            self.__class__ = self.TYPE_ONCE_APPROVED

            # Update the key of this entity.
            flat = list(self.key.flat())
            flat[-2] = str(self.__class__.__name__)
            self.key = ndb.Key(flat=flat)

            # Re-invoke iff the type has changed.
            return self._pre_put_hook()

        else:

            return super(ModeratedMixin, self)._pre_put_hook()

    def approved(self):
        """
        Override to decide how we handle failure.
        """

        return self.principal.valid

    def approve(self, reason):
        """
        Override to decide what approval means.
        """

        self.principal.validate(reason)
        assert self.approved()