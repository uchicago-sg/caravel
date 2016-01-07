from google.appengine.ext import ndb


class SchemaMixin(ndb.Expando):

    """
    A SchemaMixin tracks changes to the schema of an entity.

    >>> class F(SchemaMixin):
    ...   SCHEMA_VERSION = 1
    >>> x = F()

    >>> @F.migration(to_version=2)
    ... def bump(ent): print "bumping version for " + ent.__class__.__name__
    >>> F.SCHEMA_VERSION = 2

    >>> y = x.put().get()
    bumping version for F
    >>> y.version
    2
    """

    version = ndb.IntegerProperty(default=0)
    migrations = {}

    @classmethod
    def migration(kls, to_version):
        """
        Migrate to SCHEMA_VERSION.
        """

        def inner(func):
            kls.migrations = dict(kls.migrations)
            kls.migrations[to_version] = func
            return func
        return inner

    def run_migrations(self):
        """
        Runs all migrations on this entity until the schema version matches.
        """

        while self.version < self.SCHEMA_VERSION:
            self.version += 1
            self.migrations.get(self.version, lambda _: None)(self)

    @classmethod
    def _post_get_hook(klass, key, future):
        """
        Runs all migrations on entities grabbed via .get().
        """

        super(SchemaMixin, klass)._post_get_hook(key, future)
        if future.get_result():
            future.get_result().run_migrations()

    @classmethod
    def _from_pb(klass, *vargs, **kwargs):
        """
        Loads data coming from a protocol buffer (i.e. from Datastore).
        """
        entity = super(SchemaMixin, klass)._from_pb(*vargs, **kwargs)
        if not entity.version:
            entity.version = 0
        entity.run_migrations()
        return entity
