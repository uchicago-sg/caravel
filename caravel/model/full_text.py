from google.appengine.ext import ndb
from google.appengine.api import memcache
import json

FTS = "fts:"

def tokenize(value):
    """Parses the given string into words."""
    return value.lower().split() + [""]


class FullTextMixin(ndb.Model):
    keywords = ndb.ComputedProperty(
        lambda self: [""] + list(set(self._keywords())), repeated=True)

    @classmethod
    def matching(klass, query, offset=0, limit=None):
        """Returns entities matching the given search query."""

        # Check contents of cache.
        words = tokenize(query)
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
        for candidate in ndb.get_multi([key for key in keys if key in matches]):
            if candidate and set(words).issubset(set(candidate.keywords)):
                yield candidate

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
