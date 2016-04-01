from google.appengine.ext import ndb, db
import urllib2
import json
from caravel.storage import config


class ReplicationMixin(ndb.Model):

    """
    The ReplicatedMixin triggers a background urlfetch call to update this
    listing.
    """

    REPLICATION_URL = None

    def encode_for_replication(self):
        return self.to_dict()

    def _post_put_hook(self, future):
        """
        Write this entity to the third-party site URL.
        """

        if self.REPLICATION_URL:
            data = self.encode_for_replication()
            data["key"] = self.key.id()
            data["replication_key"] = config.replication_key

            urllib2.urlopen(self.REPLICATION_URL, json.dumps(data))

        return super(ReplicationMixin, self)._post_put_hook(future)
