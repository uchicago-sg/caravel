from google.appengine.ext import ndb

class SideEffectsMixin(ndb.Model):
    """
    The SideEffectsMixin allows an entity to have an action the first time it is
    created. This could include e.g. sending email, triggering a webhook, or
    appending something to a log.
    
    >>> class E(SideEffectsMixin):
    ...   def side_effects(self):
    ...     print "Doing something!"
    >>> x = E()
    >>> key = x.put()
    Doing something!
    >>> key = key.get().put()

    """

    run_trigger = ndb.BooleanProperty(default=False)

    def _pre_put_hook(self):
        """
        Run side_effects() the first time this entity is saved.
        """

        if not self.run_trigger:
            self.run_trigger = True
            self.side_effects()

        return super(SideEffectsMixin, self)._pre_put_hook()

    def side_effects(self):
        """
        By default, do nothing.
        """
