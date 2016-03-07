from google.appengine.ext import ndb
from google.appengine.api import memcache
import json
import itertools

FTS = "fts:"


def tokenize(value):
    """Parses the given string into words."""
    return value.lower().split()


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


class AvoidRereadingFromPBProperty(ndb.ComputedProperty):
    """
    Since ComputedPropertys are overwritten on writes anyway, we might as well
    avoid the expensive desearlization process for reads.
    """

    def _deserialize(self, ent, property, depth=1): pass


class FullTextMixin(ndb.Model):
    keywords = AvoidRereadingFromPBProperty(
        lambda self: list(set(self._keywords())), repeated=True)

    @classmethod
    def matching(klass, query, offset=0, limit=None):
        """Returns entities matching the given search query."""

        # Check contents of cache.
        words = tokenize(query)
        if not words:
            for item in klass.query().order(-klass.posted_at):
                if item._keywords():
                    yield item
            return

        results = memcache.get_multi(words, key_prefix=FTS)
        matches = None
        in_order = None
        writeback = {}

        # Fill anything missing from the initial fetch.
        for word in words:
            if word in results:
                urlsafe = json.loads(results[word])
                keys = [ndb.Key(urlsafe=val) for val in urlsafe]
            else:
                query = klass.query(klass.keywords == word)
                keys = query.order(-klass.posted_at).fetch(keys_only=True)
                writeback[word] = json.dumps([key.urlsafe() for key in keys])

            matches = (matches & set(keys)) if matches else set(keys)

        # Write back modified cache.
        memcache.set_multi(writeback, time=3600, key_prefix=FTS)

        # Elide potentially stale entries from the cache.
        keys = [key for key in keys if key in matches]

        for keys in grouper(keys, n=12):
            for entity in ndb.get_multi([key for key in keys if key]):
                if entity and set(words).issubset(set(entity.keywords)):
                    yield entity

    def _post_put_hook(self, future):
        """Clear the cache of entries maching these keywords."""

        memcache.delete_multi(self.keywords, key_prefix=FTS)

        return super(FullTextMixin, self)._post_put_hook(future)

    def _tokenize(self, field_name, value):
        """Generates a list of keywords for this entity."""

        words = tokenize(value)
        result = []
        for word in words:
            result.extend([field_name + ":" + word, word])
        return result

    def _keywords(self):
        """Override to decide what keywords to use for this entity."""

        return []
