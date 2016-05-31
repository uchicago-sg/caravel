from google.appengine.api import memcache
from google.appengine.ext import ndb


AFF = "aff:"


class Affiliation(ndb.Model):
    """
    Defines what affiliation a given principal has.
    """

    status = ndb.StringProperty(repeated=True, indexed=False)

    @classmethod
    def lookup(klass, email):
        """Look up the affiliation for the given user."""

        result = memcache.get(AFF + email)
        if result:
            return result

        ent = klass.get_by_id(email)
        if not ent:
            return None

        status = ent.status[-1]
        memcache.set(AFF + email, status)
        return status

    @classmethod
    def set(klass, email, value):
        """Marks the given user as having the given affiliation."""

        @ndb.transaction
        def txn():
            ent = klass.get_by_id(email)
            if not ent:
                ent = klass(id=email)
            ent.status.append(email)
            ent.put()

        memcache.set(AFF + email, value)


class AffiliationMixin(ndb.Model):
    """
    Marks a model as having an institutional affiliation.
    """

    _aff = None

    AFFILIATIONS = [
        ("bsd_hospital", "BSD/Hospital"),
        ("bfi_booth", "BFI/Booth"),
        ("osha_faculty_staff", "University (Non-BSD) Faculty/Staff"),
        ("osha_current_student", "University (Non-BSD) Student"),
        ("alumni", "Alumni"),
        ("hyde_parker", "Hyde Parker"),
        ("other", "Other")
    ]

    @property
    def affiliation(self):
        """Gets the affiliation of this user."""
        return Affiliation.lookup(self.principal.email)

    @affiliation.setter
    def affiliation(self, value):
        """Updates the principal's affiliation."""
        self._aff = value

    def _post_put_hook(self, future):
        """Saves the new affiliation in the datastore."""
        if self._aff:
            Affiliation.set(self.principal.email, self._aff)
        return super(AffiliationMixin, self)._post_put_hook(future)
